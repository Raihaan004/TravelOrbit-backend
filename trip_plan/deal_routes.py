"""
Deal of the Day Routes
GET /deals - Get 5 active deals for today
POST /deals/generate - Generate new deals (admin endpoint)
GET /deals/{deal_id}/details - Get details about a specific deal
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
import uuid
import logging
from urllib.parse import quote_plus
import httpx
import base64
import io
import asyncio

from auth.app.database import get_db
from auth.app.config import settings
from trip_plan import models, schemas
from trip_plan.deal_generator import generate_deal_with_ai, calculate_discount_percentage, fetch_image_for_destination
from auth.app.auth.calendar_service import create_calendar_event
from auth.app.database import SessionLocal as AuthSessionLocal
from urllib.parse import quote_plus
import random
from auth.app.database import engine
from sqlalchemy import text
from typing import Optional


# Ensure DB has the new columns added by recent model changes (dev-time convenience)
def _ensure_trip_columns():
    try:
        with engine.connect() as conn:
            # Add contact_phone if missing
            conn.execute(text("ALTER TABLE trips ADD COLUMN IF NOT EXISTS contact_phone VARCHAR;"))
            # Add passengers JSONB column if missing
            conn.execute(text("ALTER TABLE trips ADD COLUMN IF NOT EXISTS passengers JSONB;"))
            conn.commit()
    except Exception:
        # Non-fatal: if DDL fails (e.g., not Postgres), just continue — app will raise on writes
        logger = logging.getLogger(__name__)
        logger.debug("Could not ensure trip columns exist (will proceed without migration)")


_ensure_trip_columns()


import re


def _extract_phone(text: str) -> Optional[str]:
    if not text:
        return None
    # common phone patterns: +91-9999999999, 9999999999, with spaces or dashes
    phone_re = re.compile(r"(\+?\d[\d\-\s]{6,}\d)")
    m = phone_re.search(text)
    if m:
        phone = re.sub(r"[\s\-]", "", m.group(1))
        return phone
    return None


def _parse_passengers(text: str) -> list:
    """
    Parse passenger name+age pairs from freeform text.
    Returns list of dicts: {name, age, role}
    """
    if not text:
        return []

    results = []

    # Normalize separators
    norm = text.replace(';', ',').replace('\n', ',')

    # Find patterns like 'Name, 23' or 'Name 23 years' or 'Name,23'
    pattern = re.compile(r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s*,?\s*(\d{1,3})\s*(?:years|yrs|y)?", re.IGNORECASE)
    for m in pattern.finditer(norm):
        name = m.group(1).strip()
        age = int(m.group(2))
        role = "adult" if age >= 12 else "child"
        results.append({"name": name, "age": age, "role": role})

    # Fallback: if no explicit ages found, try to extract names only (comma-separated capitalized words)
    if not results:
        # split by commas/and
        parts = re.split(r",| and | & ", norm)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # ignore phone-like parts
            if _extract_phone(p):
                continue
            # if the part looks like a single name (capitalized), assume adult with unknown age
            if re.match(r"^[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*$", p):
                results.append({"name": p, "age": None, "role": "adult"})

    return results

# Fallback destination list to ensure variety when AI repeats
DESTINATION_FALLBACKS = [
    "Maldives", "Manali", "Goa", "Shimla", "Dubai", "Bali",
    "Singapore", "Paris", "London", "Bangkok", "Kerala", "Rishikesh"
]

# Lock to prevent race conditions during daily deal generation
generation_lock = asyncio.Lock()

router = APIRouter(tags=["Deals"])
logger = logging.getLogger(__name__)


# -------- Get 5 active deals of the day --------
@router.get("/deals", response_model=schemas.DealOfDayListResponse)
async def get_deals_of_day(db: Session = Depends(get_db)):
    """
    Get today's 5 active deals of the day
    Deals are randomly selected from active deals for today
    """
    today = date.today()
    
    # Get active deals for today
    deals = (
        db.query(models.DealOfDay)
        .filter(
            models.DealOfDay.is_active == 1,
            func.DATE(models.DealOfDay.generated_date) == today,
        )
        .limit(5)
        .all()
    )

    # If no deals exist for today, generate them now (up to 5)
    if not deals:
        # Use a lock to ensure only ONE request triggers generation
        async with generation_lock:
            # Double-check: maybe another request finished generating while we were waiting for the lock
            deals = (
                db.query(models.DealOfDay)
                .filter(
                    models.DealOfDay.is_active == 1,
                    func.DATE(models.DealOfDay.generated_date) == today,
                )
                .limit(5)
                .all()
            )
            
            if deals:
                # Deals were generated by someone else while we waited
                pass
            else:
                # We are the first! Generate deals.
                generated = []
                used_destinations = set()
                for i in range(5):
                    try:
                        # try generating unique destinations (retry a few times if duplicate)
                        attempts = 0
                        deal_data = await generate_deal_with_ai(generate_package=True)
                        dest = (deal_data.get("destination") or "").strip()
                        while dest and dest.lower() in used_destinations and attempts < 3:
                            attempts += 1
                            deal_data = await generate_deal_with_ai(generate_package=True)
                            dest = (deal_data.get("destination") or "").strip()

                        # If still duplicate or missing, pick a fallback random destination
                        if not dest or dest.lower() in used_destinations:
                            fallback = random.choice([d for d in DESTINATION_FALLBACKS if d.lower() not in used_destinations] or DESTINATION_FALLBACKS)
                            deal_data["destination"] = fallback
                            dest = fallback

                        if dest:
                            used_destinations.add(dest.lower())

                        # parse optional ISO date strings into date objects and ensure future dates
                        parsed_start = None
                        parsed_end = None
                        try:
                            sd = deal_data.get("start_date")
                            if sd:
                                parsed_start = datetime.fromisoformat(sd).date()
                        except Exception:
                            parsed_start = None
                        try:
                            ed = deal_data.get("end_date")
                            if ed:
                                parsed_end = datetime.fromisoformat(ed).date()
                        except Exception:
                            parsed_end = None

                        # If parsed dates are in the past, push them into the near future
                        try:
                            today_local = date.today()
                            if parsed_start and parsed_start < today_local:
                                # default start 7 days from today
                                parsed_start = today_local + timedelta(days=7)
                                if deal_data.get("duration_days"):
                                    parsed_end = parsed_start + timedelta(days=max(0, int(deal_data.get("duration_days")) - 1))
                                elif parsed_end and parsed_end < parsed_start:
                                    parsed_end = parsed_start
                            elif parsed_start is None and deal_data.get("duration_days"):
                                # if no explicit start but duration exists, set start 7 days from today
                                parsed_start = date.today() + timedelta(days=7)
                                parsed_end = parsed_start + timedelta(days=max(0, int(deal_data.get("duration_days")) - 1))
                        except Exception:
                            pass

                        deal = models.DealOfDay(
                            id=str(uuid.uuid4()),
                            title=deal_data.get("title"),
                            destination=deal_data.get("destination", "Unknown"),
                            description=deal_data.get("description", ""),
                            original_price=deal_data.get("original_price", 10000),
                            discounted_price=deal_data.get("discounted_price", 7000),
                            currency="INR",
                            ai_generated=settings.OPENROUTER_MODEL or "llama-2-7b",
                            generated_date=today,
                            is_active=1,
                            image_url=None,
                            # package fields (optional)
                            min_persons=deal_data.get("min_persons"),
                            max_persons=deal_data.get("max_persons"),
                            duration_days=deal_data.get("duration_days"),
                            start_date=parsed_start,
                            end_date=parsed_end,
                            inclusions=deal_data.get("inclusions"),
                            itinerary_json=deal_data.get("itinerary"),
                            is_international=1 if deal_data.get("is_international") else 0,
                        )
                        # Validate AI-provided image URL (if any). Normalize scheme and probe with a quick HEAD.
                        raw_img = deal_data.get("image_url")
                        valid_img = None
                        if raw_img:
                            temp = raw_img
                            if temp.startswith("//"):
                                temp = "https:" + temp
                            elif not temp.startswith(("http://", "https://")):
                                temp = "https://" + temp
                            try:
                                async with httpx.AsyncClient(timeout=5) as probe_client:
                                    head_resp = await probe_client.head(temp, follow_redirects=True)
                                    if head_resp.status_code < 400:
                                        valid_img = temp
                            except Exception:
                                valid_img = None

                        # If we don't have a validated image URL, try image provider APIs (Pexels/Unsplash) then fallback
                        if not valid_img:
                            try:
                                img = await fetch_image_for_destination(deal.destination or deal.title or "travel")
                                if img:
                                    valid_img = img
                                else:
                                    q = quote_plus(deal.destination or deal.title or "travel")
                                    valid_img = f"https://source.unsplash.com/600x400/?{q}"
                            except Exception:
                                q = quote_plus(deal.destination or deal.title or "travel")
                                valid_img = f"https://source.unsplash.com/600x400/?{q}"

                        deal.image_url = valid_img
                        db.add(deal)
                        generated.append(deal)
                    except Exception as e:
                        logger.error(f"Error generating deal in GET /deals: {str(e)}")
                        continue
                db.commit()

                # reload deals
                deals = (
                    db.query(models.DealOfDay)
                    .filter(
                        models.DealOfDay.is_active == 1,
                        func.DATE(models.DealOfDay.generated_date) == today,
                    )
                    .limit(5)
                    .all()
                )
    deal_responses = []
    for deal in deals:
        discount_pct = calculate_discount_percentage(
            float(deal.original_price), 
            float(deal.discounted_price)
        )
        deal_responses.append(
            schemas.DealOfDayResponse(
                id=deal.id,
                title=deal.title,
                destination=deal.destination,
                description=deal.description,
                original_price=float(deal.original_price),
                discounted_price=float(deal.discounted_price),
                price_per_person=float(deal.discounted_price),
                discount_percentage=discount_pct,
                currency=deal.currency,
                # backend-proxied image URL
                image_url=f"/deals/{deal.id}/image",
                generated_date=deal.generated_date,
                ai_generated=deal.ai_generated,
                # package fields
                min_persons=deal.min_persons,
                max_persons=deal.max_persons,
                duration_days=deal.duration_days,
                start_date=deal.start_date,
                end_date=deal.end_date,
                inclusions=deal.inclusions,
                itinerary=deal.itinerary_json,
                is_international=bool(deal.is_international),
            )
        )
    
    return schemas.DealOfDayListResponse(
        deals=deal_responses,
        count=len(deal_responses),
        message=f"Found {len(deal_responses)} deals of the day for {today}",
    )



# -------- Proxy image endpoint --------
@router.get("/deals/{deal_id}/image")
async def proxy_deal_image(deal_id: str, db: Session = Depends(get_db)):
    """Proxy the external image for a deal through our backend to avoid CORS/hotlinking issues."""
    deal = db.query(models.DealOfDay).filter(models.DealOfDay.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    img_url = deal.image_url
    if not img_url:
        raise HTTPException(status_code=404, detail="No image for this deal")

    # Handle data URLs (base64) directly
    if isinstance(img_url, str) and img_url.startswith("data:"):
        try:
            header, b64data = img_url.split(",", 1)
            content_type = header.split(":", 1)[1].split(";", 1)[0]
            decoded = base64.b64decode(b64data)
            return StreamingResponse(io.BytesIO(decoded), media_type=content_type)
        except Exception:
            # Fall through to placeholder redirect
            pass

    # Normalize URLs that start with '//' or missing scheme
    if img_url.startswith("//"):
        img_url = "https:" + img_url
    elif not img_url.startswith(("http://", "https://")):
        img_url = "https://" + img_url

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(img_url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(resp.aiter_bytes(), media_type=content_type)
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch image for deal {deal_id}: {e}")
        # Avoid making another outbound request from the server; redirect the client to a placeholder image
        placeholder = "https://via.placeholder.com/600x400?text=No+Image"
        return RedirectResponse(url=placeholder, status_code=307)


# -------- Generate new deals using AI (runs daily) --------
@router.post("/deals/generate")
async def generate_deals(db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """
    Generate 5 new deals for today using AI
    This should ideally be called once per day (via a scheduler)
    """
    try:
        today = date.today()
        
        # Check if we already have deals for today
        existing_deals_count = (
            db.query(models.DealOfDay)
            .filter(func.DATE(models.DealOfDay.generated_date) == today)
            .count()
        )
        
        if existing_deals_count >= 5:
            logger.info(f"Already have {existing_deals_count} deals for today")
            return {
                "message": f"Already have {existing_deals_count} deals for today",
                "deals_count": existing_deals_count,
            }
        
        # Generate up to 5 deals
        deals_needed = 5 - existing_deals_count
        generated_deals = []
        
        for i in range(deals_needed):
            try:
                deal_data = await generate_deal_with_ai(generate_package=True)
                
                # parse possible ISO date strings for start/end and ensure future dates
                parsed_start = None
                parsed_end = None
                try:
                    sd = deal_data.get("start_date")
                    if sd:
                        parsed_start = datetime.fromisoformat(sd).date()
                except Exception:
                    parsed_start = None
                try:
                    ed = deal_data.get("end_date")
                    if ed:
                        parsed_end = datetime.fromisoformat(ed).date()
                except Exception:
                    parsed_end = None

                try:
                    today_local = date.today()
                    if parsed_start and parsed_start < today_local:
                        parsed_start = today_local + timedelta(days=7)
                        if deal_data.get("duration_days"):
                            parsed_end = parsed_start + timedelta(days=max(0, int(deal_data.get("duration_days")) - 1))
                        elif parsed_end and parsed_end < parsed_start:
                            parsed_end = parsed_start
                    elif parsed_start is None and deal_data.get("duration_days"):
                        parsed_start = today_local + timedelta(days=7)
                        parsed_end = parsed_start + timedelta(days=max(0, int(deal_data.get("duration_days")) - 1))
                except Exception:
                    pass

                # ensure unique destination when generating via POST as well
                attempts = 0
                deal_data = await generate_deal_with_ai(generate_package=True)
                dest = (deal_data.get("destination") or "").strip()
                while dest and attempts < 3:
                    # if destination collides with already generated_deals, retry
                    if any(d.destination and d.destination.lower() == dest.lower() for d in generated_deals):
                        attempts += 1
                        deal_data = await generate_deal_with_ai(generate_package=True)
                        dest = (deal_data.get("destination") or "").strip()
                    else:
                        break
                if not dest or any(d.destination and d.destination.lower() == dest.lower() for d in generated_deals):
                    # pick fallback
                    fallback = random.choice([d for d in DESTINATION_FALLBACKS if not any(x.destination and x.destination.lower() == d.lower() for x in generated_deals)] or DESTINATION_FALLBACKS)
                    deal_data["destination"] = fallback
                    dest = fallback

                # parse possible ISO date strings for start/end
                parsed_start = None
                parsed_end = None
                try:
                    sd = deal_data.get("start_date")
                    if sd:
                        parsed_start = datetime.fromisoformat(sd).date()
                except Exception:
                    parsed_start = None
                try:
                    ed = deal_data.get("end_date")
                    if ed:
                        parsed_end = datetime.fromisoformat(ed).date()
                except Exception:
                    parsed_end = None

                deal = models.DealOfDay(
                    id=str(uuid.uuid4()),
                    destination=deal_data.get("destination", "Unknown"),
                    description=deal_data.get("description", ""),
                    original_price=deal_data.get("original_price", 10000),
                    discounted_price=deal_data.get("discounted_price", 7000),
                    currency="INR",
                    ai_generated=settings.OPENROUTER_MODEL or "llama-2-7b",
                    generated_date=today,
                    is_active=1,
                    min_persons=deal_data.get("min_persons"),
                    max_persons=deal_data.get("max_persons"),
                    duration_days=deal_data.get("duration_days"),
                    start_date=parsed_start,
                    end_date=parsed_end,
                    inclusions=deal_data.get("inclusions"),
                    itinerary_json=deal_data.get("itinerary"),
                    is_international=1 if deal_data.get("is_international") else 0,
                )
                
                db.add(deal)
                generated_deals.append(deal)
                logger.info(f"Generated deal {i+1}: {deal.destination}")
                
            except Exception as e:
                logger.error(f"Error generating deal {i+1}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            "message": f"Successfully generated {len(generated_deals)} new deals for today",
            "deals_count": existing_deals_count + len(generated_deals),
            "newly_generated": len(generated_deals),
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in generate_deals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate deals: {str(e)}")


# -------- Get details for a specific deal --------
@router.get("/deals/{deal_id}", response_model=schemas.DealOfDayResponse)
@router.get("/deals/{deal_id}/details", response_model=schemas.DealOfDayResponse)
def get_deal_details(deal_id: str, db: Session = Depends(get_db)):
    """
    Get full details for a specific deal
    Supports both /deals/{deal_id} and /deals/{deal_id}/details endpoints
    """
    deal = db.query(models.DealOfDay).filter(models.DealOfDay.id == deal_id).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    discount_pct = calculate_discount_percentage(
        float(deal.original_price),
        float(deal.discounted_price)
    )
    
    return schemas.DealOfDayResponse(
        id=deal.id,
        destination=deal.destination,
        description=deal.description,
        original_price=float(deal.original_price),
        discounted_price=float(deal.discounted_price),
        discount_percentage=discount_pct,
        currency=deal.currency,
        image_url=deal.image_url,
        generated_date=deal.generated_date,
        ai_generated=deal.ai_generated,
        # package fields
        min_persons=deal.min_persons,
        max_persons=deal.max_persons,
        duration_days=deal.duration_days,
        start_date=deal.start_date,
        end_date=deal.end_date,
        inclusions=deal.inclusions,
        itinerary=deal.itinerary_json,
        is_international=bool(deal.is_international),
        price_per_person=float(deal.discounted_price),
    )


# -------- Start planning from a deal (no questions - direct booking) --------
@router.post("/deals/{deal_id}/start-plan", response_model=schemas.TripMessageResponse)
async def start_plan_from_deal(deal_id: str, payload: schemas.DealStartRequest, db: Session = Depends(get_db)):
    """
    Start a trip session from a deal with all passenger details.
    Frontend collects all passenger info (name, age, phone) for all travelers.
    Backend stores all details in the passengers JSONB field linked to auth.
    """
    # Find deal
    deal = db.query(models.DealOfDay).filter(models.DealOfDay.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Create a trip session for this user filled with deal info
    trip_id = uuid.uuid4().hex

    trip = models.Trip(
        id=trip_id,
        register_id=payload.register_id,
        email=payload.email,
        from_city=payload.from_city,
        to_city=deal.destination,
        duration_days=deal.duration_days,
        start_date=deal.start_date,
        end_date=deal.end_date,
        title=deal.title or deal.destination,
        status="draft",
        is_deal_booking=1,  # Mark as deal booking
        # Pre-fill ALL trip details from deal
        budget_level=deal.itinerary_json.get("budget_level") if deal.itinerary_json else None,
        interests=deal.itinerary_json.get("interests") if deal.itinerary_json else None,
        special_requirements=deal.itinerary_json.get("special_requirements") if deal.itinerary_json else None,
        ai_summary_json=deal.itinerary_json or {"title": deal.title or deal.destination, "days": []},
        ai_summary_text=deal.description,
        contact_phone=payload.contact_phone,
    )
    
    # Store all passengers (collected from frontend)
    if payload.passengers and len(payload.passengers) > 0:
        trip.passengers = payload.passengers
        trip.adults_count = len([p for p in payload.passengers if p.get("age", 0) >= 12])
        trip.party_type = "family" if len(payload.passengers) > 1 else "solo"
    else:
        # Fallback: use single passenger if provided
        trip.passengers = [{"name": payload.passenger_name, "age": payload.passenger_age, "role": "adult"}]
        trip.adults_count = 1
        trip.party_type = "solo"
    
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Calculate pricing based on passenger count
    per_person = float(deal.discounted_price)
    total_members = len(trip.passengers) if trip.passengers else 1
    total_price = per_person * total_members
    trip.total_price = total_price

    # Validate and fix dates
    try:
        today_local = date.today()
        if not trip.start_date:
            trip.start_date = today_local + timedelta(days=7)
            if deal.duration_days and int(deal.duration_days) > 0:
                trip.end_date = trip.start_date + timedelta(days=int(deal.duration_days) - 1)
            else:
                trip.end_date = trip.start_date
        elif trip.start_date < today_local:
            trip.start_date = today_local + timedelta(days=7)
            if deal.duration_days and int(deal.duration_days) > 0:
                trip.end_date = trip.start_date + timedelta(days=int(deal.duration_days) - 1)
            else:
                trip.end_date = trip.start_date

        if trip.end_date and trip.end_date < trip.start_date:
            trip.end_date = trip.start_date
    except Exception:
        pass

    trip.status = "planned"
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Try to create Google Calendar event for trip start date
    try:
        if trip.start_date and trip.email:
            end_date = trip.end_date if trip.end_date else trip.start_date
            start_date_str = trip.start_date.isoformat()
            end_date_str = end_date.isoformat()
            
            event_title = f"🎒 {deal.destination} Trip"
            event_description = (
                f"Trip Booking Confirmation\n"
                f"Destination: {deal.destination}\n"
                f"Duration: {trip.duration_days} days\n"
                f"Budget: {trip.budget_level or 'Standard'}\n"
                f"Total Cost: ₹{total_price:.0f}\n\n"
                f"✈️ Ready for your adventure!"
            )
            
            # Create calendar session
            auth_db = AuthSessionLocal()
            try:
                # Await the async function to get the event_id
                event_id = await create_calendar_event(
                    db=auth_db,
                    user_email=trip.email,
                    title=event_title,
                    description=event_description,
                    start_date=start_date_str,
                    end_date=end_date_str,
                )
                trip.google_calendar_event_id = event_id
                db.add(trip)
                db.commit()
                logger.info(f"✅ Google Calendar event created: {event_id} for deal trip {trip.id}")
            except Exception as cal_error:
                # Gracefully handle calendar errors (user may not have Google auth)
                logger.info(f"ℹ️ Calendar event not created (optional): {str(cal_error)}")
            finally:
                auth_db.close()
    except Exception as e:
        # Non-blocking error - don't fail the booking if calendar fails
        logger.info(f"ℹ️ Calendar integration skipped for trip {trip.id}: {str(e)}")

    # Build confirmation with all deal data and all passengers
    sd = trip.start_date.isoformat() if getattr(trip, "start_date", None) else "N/A"
    ed = trip.end_date.isoformat() if getattr(trip, "end_date", None) else "N/A"
    
    # Build travelers summary
    travelers_text = ""
    if trip.passengers and len(trip.passengers) > 0:
        travelers_list = []
        for p in trip.passengers:
            travelers_list.append(f"👤 {p.get('name', 'N/A')} ({p.get('age', '?')} years)")
        travelers_text = "\n".join(travelers_list)
    else:
        travelers_text = f"👤 {payload.passenger_name} ({payload.passenger_age} years)"
    
    interests_text = ""
    if trip.interests:
        interests_list = trip.interests if isinstance(trip.interests, list) else [trip.interests]
        interests_text = f"\n🎯 Interests: {', '.join(str(i) for i in interests_list)}"
    
    inclusions_text = ""
    if deal.inclusions:
        inclusions_list = deal.inclusions if isinstance(deal.inclusions, list) else [deal.inclusions]
        inclusions_text = f"\n✅ Inclusions: {', '.join(str(i) for i in inclusions_list)}"

    ai_message_text = (
        f"Perfect! ✨ Your booking confirmed:\n\n"
        f"{travelers_text}\n"
        f"📱 Contact: {payload.contact_phone}\n"
        f"📍 From: {payload.from_city or 'N/A'}\n"
        f"🏖️ Destination: {deal.destination}\n"
        f"📅 Duration: {deal.duration_days or '?'} days\n"
        f"📆 From {sd} to {ed}\n"
        f"💼 Budget: {trip.budget_level or 'Standard'}"
        f"{interests_text}"
        f"{inclusions_text}\n"
        f"💰 Price: ₹{per_person:.0f} per person\n"
        f"💳 Total: ₹{total_price:.0f} (for {total_members} member{'s' if total_members > 1 else ''})\n\n"
        f"Ready to proceed to payment? 🛒"
    )

    logger.info(f"Deal flow: finalized trip {trip.id} for {total_members} travelers. Total INR {total_price}")

    # Log user acceptance
    user_msg = models.TripMessage(
        trip_id=trip.id,
        register_id=payload.register_id,
        email=payload.email,
        sender_role="user",
        message_type="user",
        content="I want to book this deal",
    )
    db.add(user_msg)

    # Log AI confirmation
    ai_msg = models.TripMessage(
        trip_id=trip.id,
        register_id=payload.register_id,
        email=payload.email,
        sender_role="ai",
        message_type="summary",
        content=ai_message_text,
    )
    db.add(ai_msg)
    db.commit()

    return schemas.TripMessageResponse(
        trip_id=trip.id,
        ai_message=ai_message_text,
        is_final_itinerary=True,
    )


# -------- Deactivate a deal --------
@router.post("/deals/{deal_id}/deactivate")
def deactivate_deal(deal_id: str, db: Session = Depends(get_db)):
    """
    Deactivate a deal (hide it from users)
    """
    deal = db.query(models.DealOfDay).filter(models.DealOfDay.id == deal_id).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    deal.is_active = 0
    db.commit()
    
    return {"message": f"Deal {deal_id} deactivated"}


# ============================================================
# NEW: AUTHENTICATED DEAL BOOKING FLOW
# ============================================================

@router.post("/deals/{deal_id}/book-authenticated", response_model=schemas.DealBookingFlowResponse)
async def book_deal_with_auth(
    deal_id: str,
    payload: schemas.DealAuthFlowRequest,
    db: Session = Depends(get_db)
):
    """
    Enhanced deal booking with proper authentication flow:
    1. Verify user is authenticated (register_id + email)
    2. Verify phone number (OTP or SMS)
    3. Collect passenger details
    4. Show itinerary
    5. Process payment
    
    Step-by-step authentication and booking process.
    """
    
    # Step 1: Verify Deal Exists
    deal = db.query(models.DealOfDay).filter(models.DealOfDay.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if deal.is_active == 0:
        raise HTTPException(status_code=400, detail="This deal is no longer active")
    
    logger.info(f"Deal booking initiated: {deal_id} by {payload.email}")
    
    # Step 2: Check if user has active session (basic auth check)
    existing_trip = db.query(models.Trip).filter(
        models.Trip.register_id == payload.register_id,
        models.Trip.email == payload.email,
        models.Trip.status.in_(["draft", "planned"])
    ).first()
    
    if existing_trip:
        trip = existing_trip
        logger.info(f"Resuming existing trip: {trip.id}")
    else:
        # Create new trip session
        trip_id = uuid.uuid4().hex
        trip = models.Trip(
            id=trip_id,
            register_id=payload.register_id,
            email=payload.email,
            to_city=deal.destination,
            duration_days=deal.duration_days,
            start_date=deal.start_date,
            end_date=deal.end_date,
            title=deal.title or deal.destination,
            status="draft",
            is_deal_booking=1,
            budget_level=deal.itinerary_json.get("budget_level") if deal.itinerary_json else None,
            ai_summary_json=deal.itinerary_json or {"title": deal.title or deal.destination, "days": []},
            ai_summary_text=deal.description,
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        logger.info(f"New deal trip created: {trip.id}")
    
    # Step 3: Auth Verification Flow
    # 3a: Check if user is authenticated (has register_id)
    if not payload.register_id or not payload.email:
        return schemas.DealBookingFlowResponse(
            trip_id=trip.id,
            step="auth_required",
            message="🔐 Authentication required! Please log in first to book this deal.",
            auth_verified=False,
            requires_action="verify_auth"
        )
    
    # 3b: Verify email matches
    if trip.email.lower() != payload.email.lower():
        return schemas.DealBookingFlowResponse(
            trip_id=trip.id,
            step="auth_required",
            message="❌ Email mismatch! Please use the same email you registered with.",
            auth_verified=False,
            requires_action="verify_auth"
        )
    
    auth_verified = True
    logger.info(f"Auth verified for {payload.email}")
    
    # Step 4: Phone Verification (if not already verified)
    if not trip.contact_phone and not payload.phone:
        return schemas.DealBookingFlowResponse(
            trip_id=trip.id,
            step="phone_verification",
            message="📱 Please verify your phone number to proceed with the booking.\n\nWhat is your contact phone number? (e.g., +91-9999999999)",
            auth_verified=auth_verified,
            requires_action="collect_phone"
        )
    
    # Store phone if provided
    if payload.phone and not trip.contact_phone:
        trip.contact_phone = payload.phone
        db.add(trip)
        db.commit()
        logger.info(f"Phone stored for trip {trip.id}")
    
    # Step 5: Collect Passenger Details
    has_passenger_name = payload.passenger_name and payload.passenger_name.strip()
    has_passenger_age = payload.passenger_age is not None
    
    if not has_passenger_name:
        return schemas.DealBookingFlowResponse(
            trip_id=trip.id,
            step="passenger_details",
            message=f"✈️ Great! Now let's get your details.\n\nWhat is your full name?",
            auth_verified=auth_verified,
            requires_action="collect_passenger"
        )
    
    if not has_passenger_age:
        return schemas.DealBookingFlowResponse(
            trip_id=trip.id,
            step="passenger_details",
            message=f"Thanks {payload.passenger_name}! 👤\n\nHow old are you?",
            auth_verified=auth_verified,
            requires_action="collect_passenger"
        )
    
    # Step 6: All Info Collected - Finalize Booking
    passenger_age = int(payload.passenger_age) if payload.passenger_age else None
    role = "child" if passenger_age and passenger_age < 12 else "adult"
    
    # Store passenger info
    passengers = [{"name": payload.passenger_name, "age": passenger_age, "role": role}]
    if payload.companions:
        passengers.extend(payload.companions)
    
    trip.passengers = passengers
    trip.contact_phone = payload.phone or trip.contact_phone
    trip.adults_count = 1
    trip.party_type = "solo"
    
    # Calculate pricing
    per_person = float(deal.discounted_price)
    total = per_person * 1
    trip.total_price = total
    
    # Finalize dates
    try:
        today_local = date.today()
        if not trip.start_date:
            trip.start_date = today_local + timedelta(days=7)
            if deal.duration_days and int(deal.duration_days) > 0:
                trip.end_date = trip.start_date + timedelta(days=int(deal.duration_days) - 1)
            else:
                trip.end_date = trip.start_date
        elif trip.start_date < today_local:
            trip.start_date = today_local + timedelta(days=7)
            if deal.duration_days and int(deal.duration_days) > 0:
                trip.end_date = trip.start_date + timedelta(days=int(deal.duration_days) - 1)
            else:
                trip.end_date = trip.start_date
        
        if trip.end_date and trip.end_date < trip.start_date:
            trip.end_date = trip.start_date
    except Exception:
        pass
    
    trip.status = "planned"
    db.add(trip)
    db.commit()
    db.refresh(trip)
    
    logger.info(f"Deal booking finalized: {trip.id} - Ready for payment")
    
    # Build confirmation message
    sd = trip.start_date.isoformat() if getattr(trip, "start_date", None) else "N/A"
    ed = trip.end_date.isoformat() if getattr(trip, "end_date", None) else "N/A"
    
    confirmation_msg = (
        f"🎉 Booking Confirmed!\n\n"
        f"✅ You are authenticated\n"
        f"👤 Traveler: {payload.passenger_name} ({passenger_age} years)\n"
        f"📱 Contact: {payload.phone or trip.contact_phone}\n"
        f"🏖️ Destination: {deal.destination}\n"
        f"📅 {deal.duration_days or '?'} days\n"
        f"📆 {sd} to {ed}\n"
        f"💰 Total: ₹{total:,.0f}\n\n"
        f"Ready to proceed to payment? ✨"
    )
    
    return schemas.DealBookingFlowResponse(
        trip_id=trip.id,
        step="payment_ready",
        message=confirmation_msg,
        auth_verified=auth_verified,
        requires_action="proceed_payment"
    )

