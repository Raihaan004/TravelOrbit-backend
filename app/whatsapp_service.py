"""
WhatsApp messaging service for trip confirmations
Uses Twilio WhatsApp API to send trip summaries after payment

SETUP:
------
1. Sign up at https://www.twilio.com/
2. Get your Account SID from https://www.twilio.com/console
3. Get your Auth Token from https://www.twilio.com/console
4. Set up WhatsApp Sandbox or Production phone number
5. Add to .env file:
   TWILIO_ACCOUNT_SID = your_account_sid
   TWILIO_AUTH_TOKEN = your_auth_token
   TWILIO_WHATSAPP_NUMBER = whatsapp:+1234567890

If WhatsApp is not configured, messages are skipped gracefully.
"""

import logging
from datetime import datetime
from typing import Optional
from decimal import Decimal
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

import requests
from trip_plan.models import Trip, Payment

logger = logging.getLogger(__name__)

# Load from environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
WHATSAPP_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json"

# Check if WhatsApp is properly configured
WHATSAPP_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER)

if WHATSAPP_ENABLED:
    logger.info("✅ WhatsApp service configured from environment variables")
else:
    logger.warning("⚠️ WhatsApp service not configured - add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER to .env")


def format_trip_summary(trip: Trip, payment: Payment, booking_number: str) -> str:
    """Format trip summary for WhatsApp message"""
    
    destination = trip.to_city or "Your Destination"
    from_city = trip.from_city or "Your City"
    
    # Format dates
    start_date_str = trip.start_date.strftime("%d %b %Y") if trip.start_date else "TBD"
    end_date_str = trip.end_date.strftime("%d %b %Y") if trip.end_date else "TBD"
    
    # Build message
    message = f"""
🎉 *Trip Confirmation* 🎉

Hello! Your trip is confirmed! 🎒✈️

📍 *Trip Details*
• From: {from_city}
• To: {destination}
• Duration: {trip.duration_days} days
• Travel Type: {trip.party_type or 'Not specified'}
• Budget: {trip.budget_level or 'Not specified'}

📅 *Dates*
• Start: {start_date_str}
• End: {end_date_str}

👥 *Travelers*
• Adults: {trip.adults_count or 0}
• Children: {trip.children_count or 0}
• Seniors: {trip.seniors_count or 0}

💳 *Payment Confirmed*
• Booking #: {booking_number}
• Amount: ₹{payment.amount} {payment.currency}
• Status: ✅ {payment.status.upper()}

🤝 *Party Type*
{trip.party_type.upper() if trip.party_type else 'Solo'}

📝 *Special Requests*
{trip.special_requirements or 'No special requirements'}

Check your email for the detailed itinerary and trip plan.

Thank you for booking with TravelOrbit! 🌍
Have a wonderful trip! 🛫
    """.strip()
    
    return message


async def send_trip_confirmation_whatsapp(
    trip: Trip,
    payment: Payment,
    booking_number: str,
    phone_number: Optional[str] = None
) -> bool:
    """
    Send WhatsApp message with trip confirmation after payment
    
    Args:
        trip: Trip object
        payment: Payment object
        booking_number: Booking confirmation number
        phone_number: Optional phone number (uses trip.contact_phone if not provided)
    
    Returns:
        True if sent successfully, False otherwise
    """
    
    # Check if WhatsApp is configured
    if not WHATSAPP_ENABLED:
        logger.info("ℹ️ WhatsApp service not configured - skipping")
        return False
    
    # Get phone number
    phone = phone_number or trip.contact_phone
    if not phone:
        logger.warning(f"⚠️ No phone number for trip {trip.id} - cannot send WhatsApp")
        return False
    
    # Format phone with WhatsApp prefix if needed
    if not phone.startswith("whatsapp:"):
        phone = f"whatsapp:+{phone.lstrip('+')}"
    
    # Build message
    message = format_trip_summary(trip, payment, booking_number)
    
    # Prepare Twilio API request
    url = WHATSAPP_API_URL.format(TWILIO_ACCOUNT_SID)
    
    payload = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": phone,
        "Body": message,
    }
    
    try:
        response = requests.post(
            url,
            data=payload,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ WhatsApp message sent to {phone} for trip {trip.id}")
            return True
        else:
            logger.error(f"❌ WhatsApp API error: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ WhatsApp request failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending WhatsApp: {str(e)}")
        return False


def get_whatsapp_status() -> dict:
    """Get WhatsApp service status"""
    return {
        "enabled": WHATSAPP_ENABLED,
        "configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "account_sid": TWILIO_ACCOUNT_SID[:10] + "***" if TWILIO_ACCOUNT_SID else "Not set",
    }
