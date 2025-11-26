import json
import os
from typing import Tuple, Optional, List, Dict

import httpx

from auth.app.config import settings

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
# Use a known-good model; common OpenRouter model names:
# "openrouter/auto" (recommended), "gpt-3.5-turbo", "gpt-4-turbo-preview", "claude-3-haiku", etc.
OPENROUTER_MODEL = settings.OPENROUTER_MODEL or "openrouter/auto"

SYSTEM_PROMPT = """
You are TravelOrbit AI — an expert travel itinerary planner.

Goal:
- Ask the user questions step by step to collect all required trip details
  if they are still missing.
- When you have all details, generate a FINAL day-by-day itinerary.

Required trip fields:
- from_city
- to_city
- party_type: solo, couple, friends, family
- If family: adults_count, children_count, seniors_count
- budget_level: cheap, moderate, luxury
- duration_days
- interests: subset of [adventure, sightseeing, cultural, food, nightlife, relaxation]
- special_requirements
- start_date and end_date
- mystery_preferences: { "location_type": "india" or "international", "theme": "adventure" or "nightlife" or "enjoyment" } (ONLY if user asks for a Mystery Trip)
 - Ask explicitly for number of members traveling (adults_count, children_count, seniors_count)
   when the information is missing — do not assume values.

When you reply, ALWAYS output in two sections:

1) HUMAN SECTION (for user)
- Nice friendly reply.
- When all info is collected: a creative title and full daily itinerary.
- For each place, add:
  - Google Maps link: https://www.google.com/maps/search/?api=1&query=PLACE+CITY
  - Image search link: https://www.google.com/search?q=PLACE+CITY&tbm=isch
- Suggest a hotel based on the budget level (cheap, moderate, luxury).
- Check typical weather for the destination during the travel dates. Inform the user about the expected weather and advise if it is suitable for the trip or if they need specific preparations.

2) JSON SECTION (for the backend)
After the human text, output a line with exactly:
---JSON---
Then output a JSON object:

{
  "is_final_itinerary": true or false,
  "updated_fields": {
    "from_city": "...",
    "to_city": "...",
    "party_type": "...",
    "adults_count": 2,
    "children_count": 1,
    "seniors_count": 1,
    "budget_level": "...",
    "duration_days": 5,
    "interests": ["adventure", "food"],
    "special_requirements": "...",
    "start_date": "2025-12-20",
    "end_date": "2025-12-25"
  },
  "itinerary": {
    "title": "...",
    "hotel": {
        "name": "Hotel Name",
        "rating": "4 stars",
        "price_range": "₹8000-₹12000 per night",
        "description": "Brief description",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Hotel+Name+City",
        "image_search": "https://www.google.com/search?q=Hotel+Name+City&tbm=isch"
    },
    "days": [
      {
        "day": 1,
        "title": "Explore the City of Lights – Eiffel Tower, Louvre & More",
        "activities": [
          {
            "name": "Eiffel Tower",
            "map_url": "https://www.google.com/maps/search/?api=1&query=Eiffel+Tower+Paris",
            "image_search": "https://www.google.com/search?q=Eiffel+Tower+Paris&tbm=isch",
            "time": "09:00–12:00",
            "category": "sightseeing"
          }
        ]
      }
    ]
  }
}

Rules:
- All monetary values (hotel prices, etc.) must be in Indian Rupees (INR).
- If you are still collecting information, set is_final_itinerary = false and you may omit itinerary.
- Always include updated_fields with only the fields that changed this turn.
- When ready with full plan, set is_final_itinerary = true and include itinerary.
- Do NOT put any extra text after the JSON.
Note: When beginning from a pre-made deal/package, always confirm how many people are traveling
and their composition (adults/children/seniors). After the user confirms members, produce a
concise plan summary (title, total price estimate, duration, inclusions) followed by the full
day-by-day itinerary. After the user explicitly confirms the plan, set `is_final_itinerary` true.
"""



async def call_openrouter(messages: List[Dict]) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set in environment/.env")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "TravelOrbit",
    }
    
    # Filter & validate messages: keep only the first system message and user/assistant messages
    filtered_messages = []
    system_added = False
    
    for msg in messages:
        role = msg.get("role", "").lower()
        content = msg.get("content")
        
        # Ensure role is valid (OpenRouter spec: system, user, assistant, function)
        if role not in ["system", "user", "assistant", "function"]:
            print(f"Warning: skipping message with invalid role '{role}'")
            continue
        
        # Ensure content is a string
        if not isinstance(content, str):
            try:
                content = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
            except Exception as e:
                print(f"Warning: could not serialize content: {e}")
                content = str(content)
        
        # Keep only the first system message
        if role == "system":
            if not system_added:
                filtered_messages.append({"role": "system", "content": content})
                system_added = True
        else:
            filtered_messages.append({"role": role, "content": content})
    
    if not filtered_messages:
        raise RuntimeError("No valid messages to send to OpenRouter")
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": filtered_messages,
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    print(f"DEBUG: Sending to OpenRouter - Model: {OPENROUTER_MODEL}, Messages: {len(filtered_messages)}")

    async with httpx.AsyncClient(timeout=10) as client:
      try:
          resp = await client.post(url, headers=headers, json=payload)
          resp.raise_for_status()
      except httpx.TimeoutException:
          print("OpenRouter API timed out after 10s")
          # Return a fallback message instead of crashing
          fallback_human = "I'm taking a bit too long to think. Could you please try asking that again?"
          fallback_json = {"is_final_itinerary": False, "updated_fields": {}}
          return fallback_human + "\n---JSON---\n" + json.dumps(fallback_json)
      except httpx.HTTPStatusError:
        # Log response body for debugging
        try:
          resp_body = resp.json()
        except Exception:
          resp_body = resp.text

        err_msg = f"OpenRouter API Error ({resp.status_code}): {resp_body}"
        print(err_msg)

        # If it's a payment/credits error (402), try a lighter retry with fewer tokens
        if getattr(resp, "status_code", None) == 402:
          try:
            retry_payload = dict(payload)
            retry_payload["max_tokens"] = 600
            resp2 = await client.post(url, headers=headers, json=retry_payload)
            resp2.raise_for_status()
            data2 = resp2.json()
            return data2["choices"][0]["message"]["content"]
          except Exception:
            # fallback to a deterministic assistant message so the app can continue
            fallback_human = (
              "I can't reach the AI service right now due to account credits or token limits. "
              "Meanwhile, please provide any missing trip details: number of members, names and ages of travellers, contact phone, "
              "budget level, duration, interests and preferred start date."
            )
            fallback_json = {"is_final_itinerary": False, "updated_fields": {}}
            return fallback_human + "\n---JSON---\n" + json.dumps(fallback_json)

        # Non-retryable error: raise a RuntimeError so callers can handle
        raise RuntimeError(err_msg)

      data = resp.json()
      return data["choices"][0]["message"]["content"]
def split_ai_response(content: str) -> Tuple[str, Optional[dict]]:
    """
    Split model output into human_text and JSON dict.
    Expected format:
        <human text>
        ---JSON---
        { ... }
    """
    def _strip_code_fence(s: str) -> str:
      s = s.strip()
      # Remove ```json ... ``` or ``` ... ``` fences
      if s.startswith("```") and s.endswith("```"):
        # drop fences and optional language marker
        inner = s[3:-3].lstrip('\n')
        # if language specified (e.g., ```json), remove first token
        if '\n' in inner:
          return inner.split('\n', 1)[1].strip()
        return inner.strip()
      return s

    def _extract_balanced_json(s: str) -> Optional[dict]:
      # Find first '{' then find matching closing '}' via brace counting
      if not s or '{' not in s:
        return None
      start = s.find('{')
      depth = 0
      for i in range(start, len(s)):
        ch = s[i]
        if ch == '{':
          depth += 1
        elif ch == '}':
          depth -= 1
          if depth == 0:
            candidate = s[start:i+1]
            try:
              return json.loads(candidate)
            except Exception:
              return None
      return None

    parts = content.split("---JSON---", 1)
    human_text = parts[0].strip()
    json_data = None

    if len(parts) > 1:
      tail = _strip_code_fence(parts[1])
      json_data = _extract_balanced_json(tail)

    # If no JSON after marker, try to find a JSON object in the whole content
    if json_data is None:
      # Try stripping any code fences first
      stripped = _strip_code_fence(content)
      json_data = _extract_balanced_json(stripped)

    return human_text, json_data
