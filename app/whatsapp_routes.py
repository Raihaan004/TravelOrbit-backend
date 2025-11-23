"""
WhatsApp configuration and status routes
"""

from fastapi import APIRouter
from app.whatsapp_service import get_whatsapp_status, WHATSAPP_ENABLED

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/status")
async def whatsapp_status():
    """Get WhatsApp service status"""
    return {
        "status": "active" if WHATSAPP_ENABLED else "inactive",
        "details": get_whatsapp_status()
    }


@router.get("/setup-guide")
async def whatsapp_setup_guide():
    """Get WhatsApp setup guide"""
    return {
        "service": "WhatsApp Trip Confirmation",
        "provider": "Twilio",
        "status": "ACTIVE ✅" if WHATSAPP_ENABLED else "NOT CONFIGURED ⚠️",
        "setup_steps": [
            "1. Sign up at https://www.twilio.com/",
            "2. Get your Account SID from Twilio Dashboard",
            "3. Get your Auth Token from Twilio Dashboard",
            "4. Set up WhatsApp Sandbox or Production number",
            "5. Add to .env file:",
            "   TWILIO_ACCOUNT_SID = your_sid",
            "   TWILIO_AUTH_TOKEN = your_token",
            "   TWILIO_WHATSAPP_NUMBER = whatsapp:+1234567890",
            "6. Restart the server",
            "7. Trip confirmations will auto-send via WhatsApp after payment"
        ],
        ".env_example": {
            "TWILIO_ACCOUNT_SID": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "TWILIO_AUTH_TOKEN": "your_auth_token_here",
            "TWILIO_WHATSAPP_NUMBER": "whatsapp:+1234567890"
        },
        "notes": [
            "Phone number must be in international format with country code",
            "Message is sent automatically after payment is completed",
            "User must have contact_phone in their trip record",
            "WhatsApp is optional - booking works without it",
            "If not configured, WhatsApp messages are skipped silently"
        ]
    }

