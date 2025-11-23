import uuid
from decimal import Decimal

from trip_plan.models import Trip, Payment


def calculate_price_for_trip(trip: Trip) -> tuple[Decimal, str]:
    """
    Very simple pricing logic:
    - base per person per day
    - budget multiplier
    Returns (amount, currency) where amount is in major units (INR).
    """

    # If a total price was already set (e.g., derived from a DealOfDay), prefer that
    if getattr(trip, "total_price", None) is not None:
        try:
            return Decimal(str(trip.total_price)), "INR"
        except Exception:
            # fall through to compute if conversion fails
            pass

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


# DEPRECATED: Use app.email_service.EmailService instead
# Legacy functions kept for backwards compatibility only
def build_invoice_html(trip: Trip, payment: Payment, booking_number: str) -> str:
    """DEPRECATED: Use EmailService.build_complete_email_html() instead"""
    from app.email_service import EmailService
    return EmailService._build_invoice_html(trip, payment, booking_number)


def build_ticket_html(trip: Trip, booking_number: str) -> str:
    """DEPRECATED: Use EmailService.build_complete_email_html() instead"""
    from app.email_service import EmailService
    trip_summary = EmailService._build_trip_summary_html(trip, None, booking_number)
    itinerary = EmailService._build_daily_itinerary_html(trip)
    return f"{trip_summary}{itinerary}"


def send_email_with_invoice_and_ticket(to_email: str, subject: str, html_body: str):
    """DEPRECATED: Use EmailService.send_email() instead"""
    from app.email_service import EmailService
    EmailService.send_email(to_email, subject, html_body)

