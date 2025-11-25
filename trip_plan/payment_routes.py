from decimal import Decimal
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from trip_plan.models import Trip, Payment
from app.payments.utils import calculate_price_for_trip, generate_booking_number
from app.payments.razorpay_service import get_razorpay_service
from app.email_service import send_booking_email, EmailService # Added EmailService
from app.whatsapp_service import send_trip_confirmation_whatsapp
from auth.app.auth.calendar_service import create_calendar_event
from auth.app.database import get_db as get_auth_db
import logging

router = APIRouter(tags=["Payments"])
logger = logging.getLogger(__name__)

class CreateOrderRequest(BaseModel):
    trip_id: str

class VerifyPaymentRequest(BaseModel):
    trip_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/trips/{trip_id}/payment/create-order")
async def create_payment_order(
    trip_id: str,
    db: Session = Depends(get_db),
):
    """
    Initiate Razorpay payment:
    1. Calculate price
    2. Create Razorpay Order
    3. Return order details to frontend
    """
    try:
        trip_id = trip_id.strip() # Clean up trip_id
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            logger.error(f"Trip not found: {trip_id}")
            raise HTTPException(status_code=404, detail="Trip not found")

        # Validate status
        if trip.status == "planned":
            pass
        elif trip.status == "draft" and trip.is_deal_booking:
            trip.status = "planned"
            db.add(trip)
            db.commit()
        elif trip.status == "paid":
             raise HTTPException(status_code=400, detail="Trip is already paid")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid trip status: {trip.status}")

        # Calculate price
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
            logger.error(f"Price calculation failed for trip {trip_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Price calculation failed: {str(e)}")

        # Create Razorpay Order
        rzp = get_razorpay_service()
        
        # Mock Payment Fallback
        # If Razorpay is not configured OR if it fails, we fallback to mock
        use_mock = False
        order_data = {}
        booking_number = generate_booking_number()

        if rzp:
            try:
                order_data = rzp.create_order(
                    amount=float(amount),
                    currency=currency,
                    receipt=booking_number,
                    notes={"trip_id": trip.id, "email": trip.email}
                )
            except Exception as e:
                logger.error(f"Razorpay create_order failed: {e}. Falling back to mock payment.")
                use_mock = True
        else:
            logger.warning("Razorpay not configured. Using mock payment.")
            use_mock = True

        if use_mock:
            # Generate a mock order
            order_data = {
                "id": f"order_mock_{uuid.uuid4().hex}",
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": booking_number
            }

        return {
            "order_id": order_data["id"],
            "amount": order_data["amount"], # in paise
            "currency": order_data["currency"],
            "key_id": rzp.client.auth[0] if rzp and not use_mock else "mock_key",
            "trip_id": trip.id,
            "booking_number": booking_number,
            "email": trip.email,
            "contact": trip.contact_phone or "",
            "payment_mode": "mock" if use_mock else "razorpay"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating payment order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trips/{trip_id}/payment/verify")
async def verify_payment(
    trip_id: str,
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db),
):
    """
    Verify Razorpay payment signature and finalize booking.
    """
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        rzp = get_razorpay_service()
        
        # Verify Signature
        # Check if it's a mock payment
        if request.razorpay_order_id.startswith("order_mock_"):
            # Mock verification - always success
            logger.info(f"Verifying mock payment for {trip_id}")
            pass
        elif rzp:
            try:
                rzp.verify_payment_signature(
                    request.razorpay_order_id,
                    request.razorpay_payment_id,
                    request.razorpay_signature
                )
            except Exception as e:
                logger.error(f"Signature verification failed: {e}")
                raise HTTPException(status_code=400, detail="Invalid payment signature")
        else:
             raise HTTPException(status_code=500, detail="Payment service not configured")

        # Payment Successful - Record it
        amount, currency = calculate_price_for_trip(trip) # Re-calculate to be safe or fetch from order if stored
        
        # We need a booking number. We can generate one or try to retrieve if we stored it. 
        # Since we didn't store the order-to-booking mapping, let's generate a new one or use a consistent one.
        # Ideally, we should have created the Payment record in 'pending' state earlier.
        # For simplicity, we create it now.
        booking_number = generate_booking_number()

        payment = Payment(
            trip_id=trip.id,
            register_id=trip.register_id,
            email=trip.email,
            provider="razorpay",
            provider_payment_id=request.razorpay_payment_id,
            status="succeeded",
            amount=amount,
            currency=currency,
            created_at=datetime.utcnow(),
        )
        db.add(payment)

        trip.status = "paid"
        trip.total_price = amount
        db.add(trip)
        db.commit()
        db.refresh(payment)
        db.refresh(trip)

        # Post-payment actions (Calendar, Email, WhatsApp)
        # 1. Calendar
        try:
            if trip.start_date and trip.email:
                end_date = trip.end_date if trip.end_date else trip.start_date
                event_title = f"🎒 {trip.to_city or 'Travel'} Trip - Booking #{booking_number}"
                event_description = f"Booking #{booking_number}\nPaid via Razorpay: {request.razorpay_payment_id}"
                
                event_id = await create_calendar_event(
                    db=auth_db,
                    user_email=trip.email,
                    title=event_title,
                    description=event_description,
                    start_date=trip.start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )
                trip.google_calendar_event_id = event_id
                db.add(trip)
                db.commit()
        except Exception as e:
            logger.warning(f"Calendar event creation failed: {e}")

        # 2. Email
        try:
            send_booking_email(trip, payment, booking_number, to_email=trip.email)
        except Exception as e:
            logger.error(f"Email sending failed: {e}")

        # 3. WhatsApp
        if trip.contact_phone:
            try:
                await send_trip_confirmation_whatsapp(trip, payment, booking_number)
            except Exception as e:
                logger.warning(f"WhatsApp sending failed: {e}")

        # Generate Ticket HTML for Frontend
        ticket_html = EmailService.generate_ticket_html(trip, booking_number)

        return {
            "status": "success",
            "booking_number": booking_number,
            "trip_id": trip.id,
            "ticket_html": ticket_html
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
