import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.app.database import get_db
from . import models, schemas
from .ai_planner import SYSTEM_PROMPT, call_openrouter, split_ai_response
from auth.app.config import settings
import logging

router = APIRouter(tags=["Trip Planning"])


# -------- Start a new trip session --------
@router.post("/trip-plan/session/start", response_model=schemas.TripSessionStartResponse)
def start_session(payload: schemas.TripSessionStartRequest,
                  db: Session = Depends(get_db)):
    trip_id = uuid.uuid4().hex

    trip = models.Trip(
        id=trip_id,
        register_id=payload.register_id,
        email=payload.email,
        status="draft",
    )
    db.add(trip)
    db.commit()

    return schemas.TripSessionStartResponse(trip_id=trip_id)


# -------- Chat message with AI (collect data / generate itinerary) --------
@router.post("/trip-plan/session/message", response_model=schemas.TripMessageResponse)
async def trip_message(payload: schemas.TripMessageRequest,
                       db: Session = Depends(get_db)):
    # 1) Load trip
    trip = db.query(models.Trip).filter(models.Trip.id == payload.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # 2) Save user message
    user_msg = models.TripMessage(
        trip_id=trip.id,
        register_id=payload.register_id,
        email=payload.email,
        sender_role="user",
        message_type="user",
        content=payload.message,
        created_at=datetime.utcnow(),
    )
    db.add(user_msg)
    db.commit()

    # 3) Load conversation history
    last_msgs: List[models.TripMessage] = (
        db.query(models.TripMessage)
        .filter(models.TripMessage.trip_id == trip.id)
        .order_by(models.TripMessage.created_at.asc())
        .all()
    )

    history = []
    history.append({"role": "system", "content": SYSTEM_PROMPT})

    # current context summary
    summary_bits = []
    if trip.from_city:
        summary_bits.append(f"From: {trip.from_city}")
    if trip.to_city:
        summary_bits.append(f"To: {trip.to_city}")
    if trip.party_type:
        summary_bits.append(f"Party type: {trip.party_type}")
    if trip.budget_level:
        summary_bits.append(f"Budget: {trip.budget_level}")
    if trip.duration_days:
        summary_bits.append(f"Duration: {trip.duration_days} days")
    if trip.start_date and trip.end_date:
        summary_bits.append(f"Dates: {trip.start_date} to {trip.end_date}")
    if trip.interests and isinstance(trip.interests, list):
        summary_bits.append(f"Interests: {', '.join(trip.interests)}")
    if trip.special_requirements:
        summary_bits.append(f"Special: {trip.special_requirements}")

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

    # 4) Call OpenRouter
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env")

    try:
        ai_raw = await call_openrouter(history)
    except Exception as e:
        # Log the error server-side and return structured JSON detail so frontend can inspect
        logging.exception("Error calling OpenRouter")
        raise HTTPException(status_code=502, detail={"message": "AI service error", "error": str(e)})
    human_text, json_data = split_ai_response(ai_raw)

    is_final = False

    # 5) Apply structured updates
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
    db.refresh(trip)

    # 6) Save AI message
    ai_msg = models.TripMessage(
        trip_id=trip.id,
        register_id=payload.register_id,
        email=payload.email,
        sender_role="ai",
        message_type="summary" if is_final else "ai",
        content=human_text,
        created_at=datetime.utcnow(),
    )
    db.add(ai_msg)
    db.commit()

    return schemas.TripMessageResponse(
        trip_id=trip.id,
        ai_message=human_text,
        is_final_itinerary=is_final,
    )


# -------- Get trip detail (for frontend to show planned trip) --------
@router.get("/trip-plan/{trip_id}", response_model=schemas.TripDetail)
def get_trip(trip_id: str, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


# -------- Feedback --------
@router.post("/trip-plan/{trip_id}/feedback")
def create_feedback(trip_id: str,
                    payload: schemas.FeedbackCreate,
                    db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    fb_id = uuid.uuid4().hex
    feedback = models.Feedback(
        id=fb_id,
        trip_id=trip.id,
        register_id=trip.register_id,
        email=trip.email,
        rating=payload.rating,
        comments=payload.comments,
    )
    db.add(feedback)
    db.commit()

    return {"message": "Feedback saved"}
