from fastapi import APIRouter, Request
import logging

router = APIRouter(tags=["webhook"])
logger = logging.getLogger(__name__)

@router.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend alive"}

@router.post("/salesiq")
async def salesiq_webhook(request: Request):
    """
    Handle Zoho SalesIQ Zobot Webhook.
    Zoho sends a JSON payload with session, message, etc.
    """
    try:
        payload = await request.json()
        logger.info(f"Received SalesIQ payload: {payload}")
        
        # Extract message from typical Zobot payload
        # Structure varies but often has 'data' or 'message'
        # For now, we'll just echo back or provide a default response
        
        # Example Zobot response format:
        # {
        #   "replies": [
        #     {
        #       "text": "Hello from TravelOrbit Backend!"
        #     }
        #   ]
        # }
        
        return {
            "replies": [
                {
                    "text": "Hello! I am the TravelOrbit Assistant connected via Webhook. How can I help you plan your trip?"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error processing SalesIQ webhook: {e}")
        return {
            "replies": [
                {
                    "text": "Sorry, I encountered an error processing your request."
                }
            ]
        }

@router.get("/salesiq")
def verify_salesiq():
    """
    Handle verification requests from Zoho if needed.
    """
    return {"status": "active", "message": "SalesIQ Webhook Endpoint"}
