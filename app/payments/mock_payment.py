import uuid
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText

from app.config import settings
from trip_plan.models import Trip, Payment


def calculate_price_for_trip(trip: Trip) -> tuple[Decimal, str]:
    """
    Very simple pricing logic:
    - base per person per day
    - budget multiplier
    Returns (amount, currency) where amount is in major units (INR).
    """

    if not trip.duration_days or not trip.party_type:
        raise ValueError("Trip must have duration_days and party_type before pricing")

    # Estimate number of people
    total_people = 1
    if trip.party_type == "solo":
        total_people = 1
    elif trip.party_type == "couple":
        total_people = 2
    elif trip.party_type in ("friends", "family"):
        total_people = (trip.adults_count or 0) + (trip.children_count or 0) + (trip.seniors_count or 0)
        if total_people <= 0:
            total_people = 2  # fallback

    base_per_person_per_day = 1500  # INR
    budget_multiplier = {
        "cheap": Decimal("0.8"),
        "moderate": Decimal("1.0"),
        "luxury": Decimal("1.5"),
    }.get(trip.budget_level or "moderate", Decimal("1.0"))

    days = trip.duration_days or 1
    total_amount = Decimal(base_per_person_per_day) * total_people * days * budget_multiplier
    total_amount = total_amount.quantize(Decimal("1."))  # round to whole rupee

    return total_amount, "INR"


def generate_booking_number() -> str:
    """Simple booking reference like TRIP-2025-XXXX."""
    return "TRIP-" + uuid.uuid4().hex[:8].upper()


def build_invoice_html(trip: Trip, payment: Payment, booking_number: str) -> str:
    return f"""
    <h2>TravelOrbit Invoice</h2>
    <p>Booking No: <strong>{booking_number}</strong></p>
    <p>Email: {trip.email}</p>

    <h3>Trip Details</h3>
    <ul>
      <li><strong>Title:</strong> {trip.title or "Your Custom Trip"}</li>
      <li><strong>From:</strong> {trip.from_city}</li>
      <li><strong>To:</strong> {trip.to_city}</li>
      <li><strong>Duration:</strong> {trip.duration_days} days</li>
      <li><strong>Party:</strong> {trip.party_type}</li>
      <li><strong>Budget:</strong> {trip.budget_level}</li>
    </ul>

    <h3>Payment</h3>
    <ul>
      <li><strong>Amount:</strong> {payment.amount} {payment.currency}</li>
      <li><strong>Status:</strong> {payment.status}</li>
      <li><strong>Payment ID:</strong> {payment.id}</li>
      <li><strong>Provider:</strong> {payment.provider}</li>
    </ul>
    """


def build_ticket_html(trip: Trip, booking_number: str) -> str:
    return f"""
    <h2>Your TravelOrbit Trip Ticket</h2>
    <p>Booking No: <strong>{booking_number}</strong></p>

    <p>Thank you for booking with TravelOrbit! 🎒✈️</p>

    <h3>Trip Summary</h3>
    <ul>
      <li><strong>Title:</strong> {trip.title or "Your Custom Trip"}</li>
      <li><strong>From:</strong> {trip.from_city}</li>
      <li><strong>To:</strong> {trip.to_city}</li>
      <li><strong>Start Date:</strong> {trip.start_date}</li>
      <li><strong>End Date:</strong> {trip.end_date}</li>
    </ul>

    <h3>Itinerary</h3>
    <pre style="white-space: pre-wrap;">{trip.ai_summary_text or ""}</pre>

    <p>Please keep this booking number safe. Have an amazing trip! 🌍</p>
    """


def send_email_with_invoice_and_ticket(to_email: str, subject: str, html_body: str):
    """
    Very simple SMTP mailer.
    If SMTP_* is not configured, just log and return.
    """

    if not settings.SMTP_HOST or not settings.SENDER_EMAIL:
        print("SMTP not configured, skipping email. Content would be:")
        print(html_body)
        return

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = settings.SENDER_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
