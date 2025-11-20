import httpx
from auth.app.models import GoogleTokens
from auth.app.config import settings
from datetime import datetime

GOOGLE_CALENDAR_EVENT_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


async def create_calendar_event(db, user_email, title, description, start_date, end_date):
    token = db.query(GoogleTokens).filter_by(email=user_email).first()
    if not token:
        raise Exception("No Google token stored for this user.")

    headers = {
        "Authorization": f"Bearer {token.access_token}",
        "Content-Type": "application/json"
    }

    event_data = {
        "summary": title,
        "description": description,
        "start": {"date": start_date},
        "end": {"date": end_date}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_CALENDAR_EVENT_URL, json=event_data, headers=headers)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Failed to create Google Calendar event.")

    event = response.json()
    return event["id"]
