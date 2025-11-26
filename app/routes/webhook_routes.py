from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime, date
import random

from auth.app.database import get_db
from trip_plan import models, schemas
from trip_plan.ai_planner import SYSTEM_PROMPT, call_openrouter, split_ai_response
from auth.app.config import settings

router = APIRouter(tags=["webhook"])
logger = logging.getLogger(__name__)

# --- Pydantic Models for SalesIQ Payload ---
class SalesIQVisitor(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class SalesIQSession(BaseModel):
    id: Optional[str] = None

class SalesIQPayload(BaseModel):
    visitor: Optional[SalesIQVisitor] = None
    session: Optional[SalesIQSession] = None
    message: Optional[str] = None
    chat_id: Optional[str] = None
    # Allow extra fields since SalesIQ payload can vary
    class Config:
        extra = "allow"

@router.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend alive"}

@router.post("/salesiq")
async def salesiq_webhook(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Handle Zoho SalesIQ Zobot Webhook.
    """
    try:
        logger.info(f"Received SalesIQ payload: {payload}")
        
        # Parse payload manually to handle variations
        visitor_data = payload.get("visitor", {})
        email = visitor_data.get("email")
        name = visitor_data.get("name", "Traveler")
        message_text = payload.get("message", "")
        
        # If message is empty, check if it's inside 'data'
        if not message_text and "data" in payload:
             message_text = payload["data"].get("message", "")
        
        # Ensure message_text is a string
        if isinstance(message_text, dict):
             # Sometimes SalesIQ sends message as a dict if it has metadata
             message_text = message_text.get("text", "") or str(message_text)
        elif not isinstance(message_text, str):
             message_text = str(message_text) if message_text is not None else ""

        # 1. Validate Email
        if not email:
            return {
                "action": "reply",
                "replies": [
                    {
                        "text": "Hi there! To help you plan your trip, could you please share your email address?"
                    }
                ]
            }

        # 2. Find or Create Trip Session
        # We look for the most recent active trip for this email
        trip = (
            db.query(models.Trip)
            .filter(models.Trip.email == email)
            .order_by(models.Trip.created_at.desc())
            .first()
        )

        # If no trip exists, or the last one is fully planned/paid, start a new one
        # (Simple logic: if status is 'planned' or 'paid', start new. If 'draft', continue.)
        if not trip or trip.status in ["paid", "cancelled"]:
            trip_id = uuid.uuid4().hex
            trip = models.Trip(
                id=trip_id,
                register_id=visitor_data.get("id", "salesiq_visitor"),
                email=email,
                status="draft",
                is_mystery_trip=0 
            )
            db.add(trip)
            db.commit()
            logger.info(f"Created new trip {trip_id} for {email}")
        
        # If the user explicitly says "new trip" or "start over", force a new session
        if message_text.lower().strip() in ["new trip", "start over", "plan a trip", "hi", "hello"]:
             if trip.status != "draft" or len(trip.messages) > 2: # Only restart if it's not a fresh draft
                trip_id = uuid.uuid4().hex
                trip = models.Trip(
                    id=trip_id,
                    register_id=visitor_data.get("id", "salesiq_visitor"),
                    email=email,
                    status="draft",
                    is_mystery_trip=0
                )
                db.add(trip)
                db.commit()
                logger.info(f"Forced new trip {trip_id} for {email}")

        # 3. Handle Empty Message (Trigger Event) vs User Message
        if not message_text.strip():
            # This is likely a Trigger event (e.g. "Visitor landed")
            # We should just return a Welcome message without calling AI
            logger.info("Received empty message (Trigger). Sending welcome.")
            
            # Fetch deals for the welcome message
            today = date.today()
            deals = db.query(models.DealOfDay).filter(
                models.DealOfDay.is_active == 1,
                func.DATE(models.DealOfDay.generated_date) == today
            ).limit(3).all()
            
            welcome_text = "Hi! I'm TravelOrbit. I can help you plan a custom trip or book a deal."
            
            if deals:
                welcome_text += "\n\n🔥 **Today's Top Deals:**\n"
                for d in deals:
                    welcome_text += f"• {d.destination}: ₹{d.discounted_price:,.0f}\n"
                welcome_text += "\nType 'Book [Destination]' or 'Plan a trip' to get started!"
            else:
                welcome_text += "\n\nType 'Plan a trip' to start!"

            return {
                "action": "reply",
                "replies": [
                    {
                        "text": welcome_text
                    }
                ]
            }

        # 4. Save User Message (Only if not empty)
        user_msg = models.TripMessage(
            trip_id=trip.id,
            register_id=trip.register_id,
            email=email,
            sender_role="user",
            message_type="user",
            content=message_text,
            created_at=datetime.utcnow(),
        )
        db.add(user_msg)
        db.commit()

        # 4. Build Context for AI
        last_msgs = (
            db.query(models.TripMessage)
            .filter(models.TripMessage.trip_id == trip.id)
            .order_by(models.TripMessage.created_at.asc())
            .all()
        )

        history = []
        history.append({"role": "system", "content": SYSTEM_PROMPT})

        # Add current trip context summary
        summary_bits = []
        if trip.from_city: summary_bits.append(f"From: {trip.from_city}")
        if trip.to_city: summary_bits.append(f"To: {trip.to_city}")
        if trip.party_type: summary_bits.append(f"Party type: {trip.party_type}")
        if trip.budget_level: summary_bits.append(f"Budget: {trip.budget_level}")
        if trip.duration_days: summary_bits.append(f"Duration: {trip.duration_days} days")
        if trip.start_date: summary_bits.append(f"Start Date: {trip.start_date}")
        
        if summary_bits:
            history.append({
                "role": "system",
                "content": "Current trip context: " + " | ".join(summary_bits)
            })

        for m in last_msgs:
            history.append({
                "role": "user" if m.sender_role == "user" else "assistant",
                "content": m.content,
            })

        # 5. Call AI
        if not settings.OPENROUTER_API_KEY:
             response_text = "I'm ready to help, but my AI brain (OpenRouter API Key) is missing. Please contact support."
        else:
            try:
                ai_raw = await call_openrouter(history)
                human_text, json_data = split_ai_response(ai_raw)
                
                if not human_text:
                    human_text = "I'm thinking... could you please clarify?"

                # 6. Update Trip with JSON data
                is_final = False
                if json_data:
                    updated = json_data.get("updated_fields") or {}
                    for key, value in updated.items():
                        if hasattr(trip, key) and value is not None:
                            setattr(trip, key, value)
                    
                    is_final = bool(json_data.get("is_final_itinerary"))
                    itinerary = json_data.get("itinerary")
                    
                    if itinerary and is_final:
                        trip.title = itinerary.get("title")
                        trip.ai_summary_json = itinerary
                        trip.ai_summary_text = human_text
                        trip.status = "planned"
                    
                    db.add(trip)
                    db.commit()

                response_text = human_text
                
                # --- INJECT DEALS IF RELEVANT ---
                lower_msg = message_text.lower().strip()
                # Show deals on greeting or explicit request
                if lower_msg in ["hi", "hello", "hey", "start over", "new trip", "plan a trip", "deals", "show deals"] or "deal" in lower_msg:
                    today = date.today()
                    deals = db.query(models.DealOfDay).filter(
                        models.DealOfDay.is_active == 1,
                        func.DATE(models.DealOfDay.generated_date) == today
                    ).limit(3).all()
                    
                    if deals:
                        deal_text = "\n\n🔥 **Today's Top Deals:**\n"
                        for d in deals:
                            deal_text += f"• {d.destination}: ₹{d.discounted_price:,.0f}\n"
                        deal_text += "\nType 'Book [Destination]' to grab one!"
                        
                        response_text += deal_text
                # --------------------------------

            except Exception as e:
                logger.exception("AI Error")
                response_text = "I'm having trouble connecting to my planning services. Please try again in a moment."

        # 7. Save AI Response
        ai_msg = models.TripMessage(
            trip_id=trip.id,
            register_id=trip.register_id,
            email=email,
            sender_role="ai",
            message_type="ai",
            content=response_text,
            created_at=datetime.utcnow(),
        )
        db.add(ai_msg)
        db.commit()

        # 9. Return to SalesIQ
        return {
            "action": "reply",
            "replies": [
                {
                    "text": response_text
                }
            ]
        }

    except Exception as e:
        logger.error(f"Error processing SalesIQ webhook: {e}")
        return {
            "action": "reply",
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
