from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from trip_plan.models import Trip, Payment
from app.payments.mock_payment import (
    calculate_price_for_trip,
    generate_booking_number,
    build_invoice_html,
    build_ticket_html,
    send_email_with_invoice_and_ticket,
)

router = APIRouter(tags=["Mock Payments"])


@router.post("/trips/{trip_id}/payment/mock")
def create_mock_payment(
    trip_id: str,
    db: Session = Depends(get_db),
):
    """
    Instant 'fake' payment:
    - calculates price
    - creates Payment with status 'succeeded'
    - marks trip as 'paid'
    - generates invoice + ticket
    - emails user (if SMTP configured)
    """

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.status != "planned":
        raise HTTPException(
            status_code=400,
            detail="Trip must be in 'planned' state before payment",
        )

    # 1) calculate price
    amount, currency = calculate_price_for_trip(trip)

    # 2) create payment record
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

    # 4) build invoice + ticket HTML (single email body)
    invoice_html = build_invoice_html(trip, payment, booking_number)
    ticket_html = build_ticket_html(trip, booking_number)

    full_email_html = f"""
    <html>
      <body>
        {invoice_html}
        <hr>
        {ticket_html}
      </body>
    </html>
    """

    # 5) send email
    send_email_with_invoice_and_ticket(
        to_email=trip.email,
        subject="Your TravelOrbit Trip Booking & Itinerary",
        html_body=full_email_html,
    )

    return {
        "message": "Mock payment successful. Trip marked as paid.",
        "trip_id": trip.id,
        "booking_number": booking_number,
        "payment_status": payment.status,
        "amount": str(amount),
        "currency": currency,
    }
