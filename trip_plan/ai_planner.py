import json
import os
from typing import Tuple, Optional

import httpx

from app.config import settings  # if you prefer, read env directly here


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/gpt-4.1-mini")

SYSTEM_PROMPT = """
You are TravelOrbit AI — an expert travel itinerary planner.

Goal:
- Ask questions step by step to collect all required trip details
  if they are still missing.
- When you have all details, generate a FINAL day-by-day itinerary.

Required trip fields to collect:
- From city
- To city
- Party type: solo, couple, friends, family
- If family: number of adults, children, seniors (60+)
- Budget level: cheap, moderate, luxury
- Duration in days
- Travel interests: choose from adventure, sightseeing, cultural, food, nightlife, relaxation
- Special requirements (kids, seniors, dietary, accessibility, etc.)
- Start date and end date

When you generate the final itinerary, ALWAYS output in two sections:

1) HUMAN SECTION (for user)
- A creative title for the trip.
- Nice readable day-by-day itinerary.
- Each day shows:
  - Day title
  - Main activities
  - Google Maps links
  - Google Image search links
  - Approximate times
  - Optional hotels & restaurants.

2) JSON SECTION (for the system)
After the human text, output a line with exactly:
---JSON---
Then output a single JSON object with this shape:

{
  "is_final_itinerary": true/false,
  "updated_fields": { ... },   // only fields that changed in this turn
  "itinerary": {
    "title": "...",
    "days": [
      {
        "day": 1,
        "title": "...",
        "activities": [
          {
            "name": "...",
            "map_url": "https://www.google.com/maps/search/?api=1&query=...",
            "image_search": "https://www.google.com/search?q=...&tbm=isch",
            "time": "...",
            "category": "sightseeing"
          }
        ]
      }
    ]
  }
}

Rules:
- If you are still collecting info, set "is_final_itinerary": false
  and you can omit "itinerary".
- Always include "updated_fields" with any new or clarified values.
- "updated_fields" keys must match: from_city, to_city, party_type,
  adults_count, children_count, seniors_count, budget_level,
  duration_days, interests, special_requirements, start_date, end_date.
- When final itinerary is ready, set "is_final_itinerary": true and include "itinerary".
- Never output comments after the JSON.
"""


async def call_openrouter(messages) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("Missing OPENROUTER_API_KEY in environment")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def split_ai_response(content: str) -> Tuple[str, Optional[dict]]:
    """
    Split model output into human_text and JSON dict.
    Expected format:
        <human>
        ---JSON---
        { ... }
    """
    parts = content.split("---JSON---", 1)
    human_text = parts[0].strip()
    json_data = None
    if len(parts) > 1:
        try:
            json_data = json.loads(parts[1].strip())
        except json.JSONDecodeError:
            json_data = None
    return human_text, json_data
