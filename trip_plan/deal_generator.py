"""
Deal of the Day generator using OpenRouter AI
"""
import json
import logging
import httpx
from app.config import settings
from datetime import datetime, timedelta
from typing import Optional
import random
from urllib.parse import quote_plus
from trip_plan.ai_planner import split_ai_response

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"

logger = logging.getLogger(__name__)


async def generate_deal_with_ai(generate_package: bool = True) -> dict:
    """
    Generate a deal of the day using OpenRouter AI
    If `generate_package` is True, request a full package JSON including day-by-day itinerary
    Returns a dict with package fields.
    """
    
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OpenRouter API key not configured — using local randomized fallback deals")
        # Return a randomized fallback deal immediately so /deals can generate without AI
        fallbacks = [
            {"destination": "Maldives", "is_international": True},
            {"destination": "Manali", "is_international": False},
            {"destination": "Goa", "is_international": False},
            {"destination": "Dubai", "is_international": True},
            {"destination": "Kerala", "is_international": False},
            {"destination": "Bali", "is_international": True},
            {"destination": "Shimla", "is_international": False},
        ]
        choice = random.choice(fallbacks)
        if choice.get("is_international"):
            orig = random.randint(40000, 120000)
            disc = int(orig * random.uniform(0.6, 0.85))
        else:
            orig = random.randint(15000, 50000)
            disc = int(orig * random.uniform(0.6, 0.9))
        duration = random.randint(3, 7)
        today = datetime.utcnow().date()
        start = today
        end = (today + timedelta(days=duration-1)) if duration > 1 else today
        return {
            "title": f"{choice['destination']} Special",
            "destination": choice["destination"],
            "description": f"Enjoy a {duration}-day getaway to {choice['destination']}.",
            "original_price": orig,
            "discounted_price": disc,
            "discount_percentage": round(((orig - disc) / orig) * 100, 2),
            "image_url": None,
            "min_persons": 1,
            "max_persons": 6,
            "is_international": choice.get("is_international", False),
            "duration_days": duration,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "inclusions": ["hotel", "breakfast", "airport_transfer"],
            "itinerary": {"title": f"{choice['destination']} Itinerary", "days": []},
        }
    
    if generate_package:
        prompt = """Generate a single travel DEAL PACKAGE as JSON. DO NOT ask the user any questions — produce a complete package now.
        Return ONLY valid JSON and nothing else. Keep the JSON compact: if the package would be long, shorten per-day activities to single-line summaries so the JSON stays within token limits.
        Use this exact structure:
        {
            "title": "short marketing title",
            "destination": "destination name",
            "description": "brief 1-2 sentence description",
            "original_price": 13000,
            "discounted_price": 10000,  # PER PERSON price in INR
            "discount_percentage": 23,
            "image_url": "optional image url string",
            "min_persons": 2,
            "max_persons": 6,
            "is_international": true or false,
            "duration_days": 4,
            "start_date": "2025-12-20",  # ISO date
            "end_date": "2025-12-23",
            "budget_level": "moderate", # cheap, moderate, luxury
            "interests": ["relaxation","sightseeing"],
            "special_requirements": "any special needs",
            "inclusions": ["hotel","breakfast","airport transfer"],
            "itinerary": {
                "title": "Itinerary title",
                "days": [
                    {"day": 1, "title": "Arrival & Relax", "activities": [{"name":"Arrive","time":"15:00","category":"arrival","map_url":"...","image_search":"..."}]}
                ]
            }
        }

        Make the package plausible and realistic. Prices should be in INR. If the destination is international, set is_international true.
        If you are unsure about dates, pick a reasonable upcoming start date within the next 90 days and compute end_date from duration_days.
        Keep the JSON compact and valid. If you cannot fill a field, choose a sensible default rather than asking the user. Do not output any extra text outside the JSON."""
    else:
        prompt = """Generate a single travel deal of the day as JSON. 
        Return ONLY valid JSON with this structure:
        {
            "title": "short marketing title (e.g., Romantic Maldives Getaway)",
            "destination": "destination name (e.g., Maldives)",
            "description": "brief 1-2 sentence description of the destination",
            "original_price": 13000,
            "discounted_price": 10000,
            "discount_percentage": 23,
            "image_url": "optional image url string"
        }
        Make the destination and prices realistic and varied. All prices are in INR."""
    
    logger.info(f"AI: generate_deal_with_ai called (generate_package={generate_package})")
    try:
        system_msg = (
            "You are an assistant that MUST return a single valid JSON object and nothing else. "
            "Do NOT include any explanatory text, headings, or markdown. Return only the JSON package matching the requested schema."
        )

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://travelorbit.com",
                    "X-Title": "TravelOrbit Deal Generator",
                },
                json={
                    "model": settings.OPENROUTER_MODEL or "meta-llama/llama-2-7b-chat",
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                }
            )

        response.raise_for_status()
        data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        logger.info("AI: received response from OpenRouter (truncated)")
        logger.debug(str(content)[:1000])

        # Try to parse using the shared robust splitter (handles code fences and balanced JSON)
        deal_data = None
        try:
            _, maybe_json = split_ai_response(content)
            if isinstance(maybe_json, dict):
                maybe = maybe_json
                keys = set(maybe.keys())
                if {"destination", "discounted_price"}.issubset(keys):
                    deal_data = maybe
                elif "itinerary" in maybe and isinstance(maybe.get("itinerary"), dict):
                    deal_data = {
                        "title": maybe.get("title") or f"{maybe.get('itinerary', {}).get('title','Package')}",
                        "destination": maybe.get("destination", "Unknown"),
                        "description": maybe.get("description", ""),
                        "original_price": maybe.get("original_price", 10000),
                        "discounted_price": maybe.get("discounted_price", 7000),
                        "discount_percentage": maybe.get("discount_percentage", 0),
                        "image_url": maybe.get("image_url"),
                        "min_persons": maybe.get("min_persons"),
                        "max_persons": maybe.get("max_persons"),
                        "duration_days": maybe.get("duration_days"),
                        "start_date": maybe.get("start_date"),
                        "end_date": maybe.get("end_date"),
                        "budget_level": maybe.get("budget_level"),
                        "interests": maybe.get("interests"),
                        "special_requirements": maybe.get("special_requirements"),
                        "inclusions": maybe.get("inclusions"),
                        "itinerary": maybe.get("itinerary"),
                        "is_international": maybe.get("is_international", False),
                    }
        except Exception:
            deal_data = None

        # If still not found, attempt to repair a possibly truncated JSON by appending closing braces.
        # This can salvage responses that were cut off due to token limits.
        if deal_data is None:
            try:
                # Try a safe truncate-fix: find first '{' and attempt to balance braces by appending '}'s
                if isinstance(content, str) and '{' in content:
                    start = content.find('{')
                    depth = 0
                    for ch in content[start:]:
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                    if depth > 0:
                        candidate = content[start:].strip()
                        candidate_fixed = candidate + ('}' * depth)
                        try:
                            deal_data = json.loads(candidate_fixed)
                            logger.info('AI: repaired truncated JSON by appending %d closing braces', depth)
                        except Exception:
                            deal_data = None
            except Exception:
                deal_data = None

        # If still not found, retry once with a clarifying instruction
        if deal_data is None:
            logger.warning("AI: response did not contain valid JSON — retrying once with clarification")
            followup_prompt = "Previous response did not include valid JSON. Return ONLY valid JSON matching the schema exactly and nothing else. If uncertain pick reasonable defaults. Return the JSON alone or inside a code fence but do not add extra commentary."
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp2 = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "HTTP-Referer": "https://travelorbit.com",
                            "X-Title": "TravelOrbit Deal Generator - Retry",
                        },
                        json={
                            "model": settings.OPENROUTER_MODEL or "meta-llama/llama-2-7b-chat",
                            "messages": [{"role": "user", "content": followup_prompt}],
                            "temperature": 0.1,
                            "max_tokens": 2000,
                        }
                    )
                resp2.raise_for_status()
                data2 = resp2.json()
                content2 = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.debug("AI retry raw content (truncated): %s", str(content2)[:1000])
                # Try again with the robust splitter
                try:
                    _, maybe_json2 = split_ai_response(content2)
                    if isinstance(maybe_json2, dict):
                        maybe = maybe_json2
                        keys = set(maybe.keys())
                        if {"destination", "discounted_price"}.issubset(keys):
                            deal_data = maybe
                        elif "itinerary" in maybe and isinstance(maybe.get("itinerary"), dict):
                            deal_data = {
                                "title": maybe.get("title") or f"{maybe.get('itinerary', {}).get('title','Package')}",
                                "destination": maybe.get("destination", "Unknown"),
                                "description": maybe.get("description", ""),
                                "original_price": maybe.get("original_price", 10000),
                                "discounted_price": maybe.get("discounted_price", 7000),
                                "discount_percentage": maybe.get("discount_percentage", 0),
                                "image_url": maybe.get("image_url"),
                                "min_persons": maybe.get("min_persons"),
                                "max_persons": maybe.get("max_persons"),
                                "duration_days": maybe.get("duration_days"),
                                "start_date": maybe.get("start_date"),
                                "end_date": maybe.get("end_date"),
                                "budget_level": maybe.get("budget_level"),
                                "interests": maybe.get("interests"),
                                "special_requirements": maybe.get("special_requirements"),
                                "inclusions": maybe.get("inclusions"),
                                "itinerary": maybe.get("itinerary"),
                                "is_international": maybe.get("is_international", False),
                            }
                except Exception:
                    deal_data = None
            except Exception as e:
                logger.debug(f"Retry to OpenRouter failed: {e}")

        if deal_data is None:
            logger.error(
                "AI: No JSON found in response. Raw response (truncated): "
                f"{str(content)[:1000]}"
            )
            raise ValueError("No JSON found in AI response")

        # Normalize returned fields and provide defaults
        # Normalize returned fields and provide defaults
        title_val = deal_data.get("title")
        dest_val = deal_data.get("destination") or title_val or "Unknown"

        image_val = deal_data.get("image_url")
        if not image_val and dest_val and dest_val != "Unknown":
            # fallback to Unsplash source for visuals
            image_val = f"https://source.unsplash.com/600x400/?{quote_plus(dest_val)}"

        result = {
            "title": title_val,
            "destination": dest_val,
            "description": deal_data.get("description", ""),
            "original_price": float(deal_data.get("original_price", 10000)),
            # discounted_price is interpreted as per-person price
            "discounted_price": float(deal_data.get("discounted_price", 7000)),
            "discount_percentage": float(deal_data.get("discount_percentage", 0)),
            "image_url": image_val,
            "min_persons": int(deal_data.get("min_persons", 2)) if deal_data.get("min_persons") is not None else 2,
            "max_persons": int(deal_data.get("max_persons")) if deal_data.get("max_persons") is not None else None,
            "duration_days": int(deal_data.get("duration_days")) if deal_data.get("duration_days") is not None else None,
            "start_date": deal_data.get("start_date"),
            "end_date": deal_data.get("end_date"),
            "budget_level": deal_data.get("budget_level"),
            "interests": deal_data.get("interests"),
            "special_requirements": deal_data.get("special_requirements"),
            "inclusions": deal_data.get("inclusions"),
            "itinerary": deal_data.get("itinerary"),
            "is_international": bool(deal_data.get("is_international", False)),
        }
        return result
    except Exception as e:
        logger.error(f"Error generating deal with AI: {str(e)}")
        # Return a randomized fallback deal so daily lists aren't identical
        fallbacks = [
            {"destination": "Maldives", "is_international": True},
            {"destination": "Manali", "is_international": False},
            {"destination": "Goa", "is_international": False},
            {"destination": "Dubai", "is_international": True},
            {"destination": "Kerala", "is_international": False},
            {"destination": "Bali", "is_international": True},
            {"destination": "Shimla", "is_international": False},
        ]
        choice = random.choice(fallbacks)
        # Generate varied prices based on international/domestic
        if choice.get("is_international"):
            orig = random.randint(40000, 120000)
            disc = int(orig * random.uniform(0.6, 0.85))
        else:
            orig = random.randint(15000, 50000)
            disc = int(orig * random.uniform(0.6, 0.9))

        # random duration and inclusions
        duration = random.randint(3, 7)
        today = datetime.utcnow().date()
        start = today
        end = (today + timedelta(days=duration-1)) if duration > 1 else today

        return {
            "title": f"{choice['destination']} Special",
            "destination": choice["destination"],
            "description": f"Enjoy a {duration}-day getaway to {choice['destination']}.",
            "original_price": orig,
            "discounted_price": disc,
            "discount_percentage": round(((orig - disc) / orig) * 100, 2),
            "image_url": None,
            "min_persons": 1,
            "max_persons": 6,
            "is_international": choice.get("is_international", False),
            "duration_days": duration,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "inclusions": ["hotel", "breakfast", "airport_transfer"],
            "itinerary": {"title": f"{choice['destination']} Itinerary", "days": []},
        }


async def fetch_image_for_destination(destination: str) -> Optional[str]:
    """
    Try to fetch an image URL for a destination using Pexels or Unsplash APIs (if keys provided).
    Returns a URL string or None.
    """
    if not destination:
        return None

    # Try Pexels first if API key provided
    pexels_key = getattr(settings, "PEXELS_API_KEY", None)
    if pexels_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(PEXELS_SEARCH_URL, params={"query": destination, "per_page": 1}, headers={"Authorization": pexels_key})
            if res.status_code == 200:
                data = res.json()
                photos = data.get("photos") or []
                if photos:
                    src = photos[0].get("src", {})
                    return src.get("large") or src.get("original")
        except Exception as e:
            logger.debug(f"Pexels image lookup failed: {e}")

    # Try Unsplash if access key provided
    unsplash_key = getattr(settings, "UNSPLASH_ACCESS_KEY", None)
    if unsplash_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(UNSPLASH_SEARCH_URL, params={"query": destination, "per_page": 1}, headers={"Authorization": f"Client-ID {unsplash_key}"})
            if res.status_code == 200:
                data = res.json()
                results = data.get("results") or []
                if results:
                    return results[0].get("urls", {}).get("regular")
        except Exception as e:
            logger.debug(f"Unsplash image lookup failed: {e}")

    return None


def calculate_discount_percentage(original: float, discounted: float) -> float:
    """Calculate discount percentage"""
    if original == 0:
        return 0
    return round(((original - discounted) / original) * 100, 2)
