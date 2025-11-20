from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.app.database import get_db
from trip_plan.models import Trip
from auth.app.auth.calendar_service import create_calendar_event

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.post("/create/{trip_id}")
async def attach_calendar(trip_id: str, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter_by(trip_id=trip_id).first()

    if not trip:
        return {"error": "Trip not found"}

    if not trip.start_date or not trip.end_date:
        return {"error": "Trip dates missing"}

    event_id = await create_calendar_event(
        db=db,
        user_email=trip.email,
        title=trip.title,
        description=trip.ai_summary_text,
        start_date=str(trip.start_date),
        end_date=str(trip.end_date)
    )

    trip.google_calendar_event_id = event_id
    db.commit()

    return {"message": "Google Calendar event created", "event_id": event_id}
