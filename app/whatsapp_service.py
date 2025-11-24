"""
WhatsApp messaging service for trip confirmations
Currently disabled as Twilio has been replaced with Fast2SMS for OTPs.
Fast2SMS does not support WhatsApp API in the same way.
"""

import logging
from typing import Optional
from trip_plan.models import Trip, Payment

logger = logging.getLogger(__name__)

# WhatsApp service disabled
WHATSAPP_ENABLED = False

logger.info("ℹ️ WhatsApp service is currently disabled (Twilio removed)")


def format_trip_summary(trip: Trip, payment: Payment, booking_number: str) -> str:
    """Format trip summary for WhatsApp message (Placeholder)"""
    return ""


async def send_trip_confirmation_whatsapp(
    trip: Trip,
    payment: Payment,
    booking_number: str,
    phone_number: Optional[str] = None
) -> bool:
    """
    Send WhatsApp message with trip confirmation after payment
    (Disabled)
    """
    logger.info("ℹ️ WhatsApp service disabled - skipping message")
    return False


def get_whatsapp_status() -> dict:
    """Get WhatsApp service status"""
    return {
        "enabled": False,
        "configured": False,
        "message": "Service disabled (Twilio removed)"
    }
