from decimal import Decimal
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from trip_plan.models import Trip, Payment
from app.payments.mock_payment import (
    calculate_price_for_trip,
    generate_booking_number,
)
from app.email_service import send_booking_email
from app.whatsapp_service import send_trip_confirmation_whatsapp
from auth.app.auth.calendar_service import create_calendar_event
from auth.app.database import get_db as get_auth_db
import logging

router = APIRouter(tags=["Mock Payments"])
logger = logging.getLogger(__name__)


class MockPaymentRequest(BaseModel):
    """Optional request body for mock payment endpoint"""
    members_count: Optional[int] = None
    additional_notes: Optional[str] = None


@router.post("/trips/{trip_id}/payment/mock")
async def create_mock_payment(
    trip_id: str,
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db),
    request_body: Optional[MockPaymentRequest] = Body(default=None),
):
    """
    Instant 'fake' payment:
    - calculates price
    - creates Payment with status 'succeeded'
    - marks trip as 'paid'
    - generates invoice + ticket
    - creates Google Calendar event for trip start date
    - emails user (if SMTP configured)
    """
    try:
        # Validate trip_id format
        if not trip_id or not isinstance(trip_id, str):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trip ID format: {trip_id}"
            )

        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip not found with ID: {trip_id}"
            )

        # Allow payment for:
        # 1. Trips in "planned" status (regular flow)
        # 2. Deal bookings in "draft" status (they're pre-planned from deal data)
        if trip.status == "planned":
            # Already planned, proceed normally
            pass
        elif trip.status == "draft" and trip.is_deal_booking:
            # Deal booking in draft - auto-transition to planned for payment
            logger.info(f"ℹ️ Auto-transitioning deal booking {trip.id} from draft to planned")
            trip.status = "planned"
            db.add(trip)
            db.commit()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Trip must be in 'planned' state before payment. Current status: {trip.status}. Please finalize your trip details first.",
            )

        # 1) calculate price
        try:
            # For deal bookings, ensure we have total_price set
            if trip.is_deal_booking and not trip.total_price:
                # Recalculate if missing
                if not trip.party_type and trip.passengers:
                    trip.party_type = "family" if len(trip.passengers) > 1 else "solo"
                    db.add(trip)
                    db.commit()
            
            amount, currency = calculate_price_for_trip(trip)
        except Exception as e:
            logger.error(f"❌ Price calculation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate price for trip: {str(e)}"
            )

        # 2) create payment record
        try:
            booking_number = generate_booking_number()
            fake_provider_payment_id = "MOCKPAY-" + booking_number

            payment = Payment(
                trip_id=trip.id,
                register_id=trip.register_id,
                email=trip.email,
                provider="mock",
                provider_payment_id=fake_provider_payment_id,
                status="succeeded",  # INSTANT SUCCESS
                amount=amount,
                currency=currency,
                created_at=datetime.utcnow(),
            )
            db.add(payment)

            # 3) update trip status + total_price
            trip.status = "paid"
            trip.total_price = amount
            db.add(trip)

            db.commit()
            db.refresh(payment)
            db.refresh(trip)
            logger.info(f"✅ Payment created successfully: {payment.id} for trip {trip.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Payment creation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create payment record: {str(e)}"
            )

        # 4) Try to create Google Calendar event for trip start date
        try:
            if trip.start_date and trip.email:
                # Calculate end date for calendar event
                end_date = trip.end_date if trip.end_date else trip.start_date
                
                # Format dates as strings (YYYY-MM-DD)
                start_date_str = trip.start_date.isoformat()
                end_date_str = end_date.isoformat()
                
                # Create event title and description
                destination = trip.to_city or "Travel"
                event_title = f"🎒 {destination} Trip - Booking #{booking_number}"
                
                event_description = (
                    f"Booking Confirmation\n"
                    f"Booking #: {booking_number}\n"
                    f"Destination: {destination}\n"
                    f"Duration: {trip.duration_days} days\n"
                    f"Party Type: {trip.party_type or 'Not specified'}\n"
                    f"Budget Level: {trip.budget_level or 'Not specified'}\n"
                    f"Total Cost: {currency} {amount}\n"
                    f"\nReady for your adventure! ✈️"
                )
                
                # Create calendar event
                try:
                    event_id = await create_calendar_event(
                        db=auth_db,
                        user_email=trip.email,
                        title=event_title,
                        description=event_description,
                        start_date=start_date_str,
                        end_date=end_date_str,
                    )
                    
                    # Store event ID in trip for future reference
                    trip.google_calendar_event_id = event_id
                    db.add(trip)
                    db.commit()
                    
                    logger.info(f"✅ Google Calendar event created: {event_id} for trip {trip.id}")
                except Exception as cal_error:
                    # Gracefully handle calendar errors (user may not have Google auth)
                    logger.info(f"ℹ️ Calendar event not created (optional): {str(cal_error)}")
                
        except Exception as e:
            # Non-blocking error - don't fail payment if calendar fails
            logger.info(f"ℹ️ Calendar integration skipped for trip {trip.id}: {str(e)}")
            # Don't fail payment if calendar creation fails
            pass

        # 5) Send optimized email with complete itinerary and traveler details
        try:
            send_booking_email(trip, payment, booking_number, to_email=trip.email)
            logger.info(f"✅ Booking email sent to {trip.email}")
        except Exception as e:
            logger.error(f"⚠️ Email sending failed (non-blocking): {str(e)}")

        # 6) Send WhatsApp confirmation message (if phone available)
        if trip.contact_phone:
            try:
                await send_trip_confirmation_whatsapp(trip, payment, booking_number)
                logger.info(f"✅ WhatsApp notification sent to {trip.contact_phone}")
            except Exception as e:
                logger.info(f"ℹ️ WhatsApp notification skipped: {str(e)}")
        
        return {
            "message": "Mock payment successful. Trip marked as paid.",
            "trip_id": trip.id,
            "booking_number": booking_number,
            "payment_status": payment.status,
            "amount": str(amount),
            "currency": currency,
            "calendar_event_id": trip.google_calendar_event_id,
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in create_mock_payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during payment processing: {str(e)}"
        )
