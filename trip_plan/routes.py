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
from decimal import Decimal
from typing import Dict, Optional

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

    # Validate and set email
    if not payload.email:
        payload.email = trip.email or "user@example.com"

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

    # 3) If this is a deal booking and already planned, don't call AI
    if trip.is_deal_booking and trip.status == "planned":
        # Just acknowledge and don't call AI
        ai_message_text = "Thank you! Your booking is confirmed. Proceed to payment whenever you're ready."
        ai_msg = models.TripMessage(
            trip_id=trip.id,
            register_id=payload.register_id,
            email=payload.email,
            sender_role="ai",
            message_type="ai",
            content=ai_message_text,
        )
        db.add(ai_msg)
        db.commit()
        return schemas.TripMessageResponse(
            trip_id=trip.id,
            ai_message=ai_message_text,
            is_final_itinerary=True,
        )

    # 4) Load conversation history
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

    # 5) Call OpenRouter
    if not settings.OPENROUTER_API_KEY:
        # Fallback AI response if no OpenRouter configured
        fallback_message = """I'm helping you plan your trip! To get started, please tell me:

1. **Where are you traveling from?** (e.g., New York, London, etc.)
2. **Where do you want to go?** (destination city/country)
3. **How many people are traveling?** (solo, couple, family, etc.)
4. **How long is your trip?** (number of days)
5. **What's your budget?** (cheap, moderate, luxury)
6. **What interests you?** (adventure, sightseeing, cultural, food, nightlife, relaxation)

Once you share these details, I'll create a personalized day-by-day itinerary for you! ✈️"""
        
        ai_msg = models.TripMessage(
            trip_id=trip.id,
            register_id=payload.register_id,
            email=payload.email,
            sender_role="ai",
            message_type="ai",
            content=fallback_message,
            created_at=datetime.utcnow(),
        )
        db.add(ai_msg)
        db.commit()
        return schemas.TripMessageResponse(
            trip_id=trip.id,
            ai_message=fallback_message,
            is_final_itinerary=False,
        )

    try:
        ai_raw = await call_openrouter(history)
    except Exception as e:
        # Log the error server-side and return structured JSON detail so frontend can inspect
        logging.exception("Error calling OpenRouter")
        fallback_message = f"""I encountered an issue reaching the AI planning service. Could you please share:
- Your destination
- Trip duration (days)
- Budget level (cheap/moderate/luxury)
- Number of travelers
- Your interests (adventure, food, culture, etc.)

I'll help you plan your trip once these details are confirmed!"""
        
        ai_msg = models.TripMessage(
            trip_id=trip.id,
            register_id=payload.register_id,
            email=payload.email,
            sender_role="ai",
            message_type="ai",
            content=fallback_message,
            created_at=datetime.utcnow(),
        )
        db.add(ai_msg)
        db.commit()
        return schemas.TripMessageResponse(
            trip_id=trip.id,
            ai_message=fallback_message,
            is_final_itinerary=False,
        )
    
    human_text, json_data = split_ai_response(ai_raw)

    # If parsing failed or no human text, provide fallback
    if not human_text or human_text.strip() == "":
        human_text = """Let me help you plan your trip step by step! Please share:
- Your destination and departure city
- Trip duration and preferred dates
- Number and type of travelers
- Budget level and interests

I'll create a personalized itinerary for you!"""

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


# ----- Package generation + selection -----
def _estimate_people(trip: models.Trip) -> int:
    if not trip.party_type:
        return 1
    if trip.party_type == "solo":
        return 1
    if trip.party_type == "couple":
        return 2
    # friends or family
    total = (trip.adults_count or 0) + (trip.children_count or 0) + (trip.seniors_count or 0)
    return total if total > 0 else 2


def generate_packages(trip: models.Trip, budget_override: Optional[str] = None) -> list[Dict]:
    budget = (budget_override or trip.budget_level or "moderate").lower()
    days = trip.duration_days or 1
    people = _estimate_people(trip)

    base_per_person_per_day = 1500  # keep in sync with app.payments.utils

    budget_ranges = {
        "cheap": (0.7, 0.95),
        "moderate": (1.0, 1.3),
        "luxury": (1.5, 2.0),
    }

    min_mult, max_mult = budget_ranges.get(budget, budget_ranges["moderate"])

    package_types = [
        ("Essential", 0.0),
        ("Comfort", 0.05),
        ("Premium", 0.12),
        ("All-Inclusive", 0.2),
    ]

    packages = []
    for name, extra in package_types:
        # vary multipliers slightly per package
        p_min = min_mult + extra
        p_max = max_mult + extra

        # Determine hotel based on budget AND package type
        current_hotel = "Standard Hotel"
        if budget == "cheap":
             if name == "Essential": current_hotel = "Budget Stay / Hostel"
             elif name == "Comfort": current_hotel = "2-Star Hotel"
             elif name == "Premium": current_hotel = "3-Star Hotel"
             elif name == "All-Inclusive": current_hotel = "3-Star Hotel + Meals"
        elif budget == "moderate":
             if name == "Essential": current_hotel = "3-Star Hotel"
             elif name == "Comfort": current_hotel = "3-Star Premium Hotel"
             elif name == "Premium": current_hotel = "4-Star Hotel"
             elif name == "All-Inclusive": current_hotel = "4-Star Hotel + All Meals"
        elif budget == "luxury":
             if name == "Essential": current_hotel = "4-Star Hotel"
             elif name == "Comfort": current_hotel = "5-Star Hotel"
             elif name == "Premium": current_hotel = "5-Star Luxury Resort"
             elif name == "All-Inclusive": current_hotel = "5-Star Resort + All Meals"

        min_price = int(Decimal(base_per_person_per_day) * Decimal(people) * Decimal(days) * Decimal(p_min))
        max_price = int(Decimal(base_per_person_per_day) * Decimal(people) * Decimal(days) * Decimal(p_max))

        packages.append({
            "id": uuid.uuid4().hex,
            "name": f"{budget.title()} {name}",
            "description": f"{name} package. Includes {current_hotel}.",
            "min_price": max(1, min_price),
            "max_price": max(1, max_price),
        })

    return packages


@router.get("/trip-plan/{trip_id}/packages", response_model=schemas.PackageListResponse)
def list_packages(trip_id: str, budget: Optional[str] = None, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not (trip.duration_days and trip.party_type):
        raise HTTPException(status_code=400, detail="Trip must have duration_days and party_type to generate packages")

    packages = generate_packages(trip, budget_override=budget)

    return schemas.PackageListResponse(trip_id=trip.id, budget_level=budget or trip.budget_level, packages=packages)


@router.post("/trip-plan/{trip_id}/packages/{package_id}/select", response_model=schemas.PackageSelectResponse)
def select_package(trip_id: str, package_id: str, payload: schemas.PackageSelectRequest, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not (trip.duration_days and trip.party_type):
        raise HTTPException(status_code=400, detail="Trip must have duration_days and party_type to select a package")

    # regenerate packages with current trip budget
    packages = generate_packages(trip)
    selected = None
    for p in packages:
        if p["id"] == package_id:
            selected = p
            break

    if not selected:
        raise HTTPException(status_code=404, detail="Package not found")

    # choose a concrete price (median)
    chosen_price = (selected["min_price"] + selected["max_price"]) // 2

    # store selection in ai_summary_json for now
    ai_json = trip.ai_summary_json or {}
    ai_json["selected_package"] = selected

    trip.ai_summary_json = ai_json
    trip.status = "planned"
    trip.total_price = chosen_price

    db.add(trip)
    db.commit()
    db.refresh(trip)

    next_step = f"/trips/{trip.id}/payment/mock"

    return schemas.PackageSelectResponse(
        message="Package selected. Proceed to payment.",
        trip_id=trip.id,
        selected_package=selected,
        next_step=next_step,
    )


# -------- Get trip detail (for frontend to show planned trip) --------
@router.get("/trip-plan/{trip_id}", response_model=schemas.TripDetail)
def get_trip(trip_id: str, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


# -------- Update Passengers --------
@router.post("/trip-plan/{trip_id}/passengers")
def update_passengers(trip_id: str,
                      payload: schemas.TripPassengersUpdate,
                      db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Update passengers
    trip.passengers = payload.passengers
    if payload.contact_phone:
        trip.contact_phone = payload.contact_phone
    
    # Update ownership if changed (e.g. guest -> logged in user)
    if payload.register_id:
        trip.register_id = payload.register_id
    if payload.email:
        trip.email = payload.email
    
    # Also update counts based on passengers list if needed
    # For now, we just store the list
    
    db.add(trip)
    db.commit()
    
    return {"message": "Passengers updated successfully"}


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
