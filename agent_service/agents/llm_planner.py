import os
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

try:
    from providers.base import PlaceItem, ActivityOption, DayPlan, DayByDayPlan
except (ImportError, ModuleNotFoundError):
    from agent_service.providers.base import PlaceItem, ActivityOption, DayPlan, DayByDayPlan

logger = logging.getLogger("llm_planner")

# Capped exponential backoff delays (seconds) for 503/429 retries
BACKOFF_DELAYS = [2, 4]

DEFAULT_THEMES = [
    "Arrival, Old Town Orientation & Scenic Welcome",
    "World-Class Art & Architectural Wonders",
    "Vibrant Food Markets & Culinary Immersion",
    "Panoramic City Views & Cultural Sights",
    "Hidden Courtyards, Boutiques & Local Craft",
    "Botanical Nature Walk & Twilight River Cruise",
    "Historic Landmarks & Grand Cathedral Quarter",
    "Contemporary Arts, Design & Modern Living",
    "Culinary Workshop & Gourmet Tasting Journey",
    "Leisurely Farewell & Iconic Souvenir Exploration"
]

def create_rule_based_plan(
    candidate_places: List[PlaceItem],
    trip_days: int,
    destination: str,
    per_day_budget: float
) -> DayByDayPlan:
    """
    Distributes candidate places evenly across the trip days in a logical
    morning/afternoon/evening schedule respecting the daily activity budget.
    """
    days: List[DayPlan] = []
    dest_title = destination.strip().title()

    if not candidate_places:
        candidate_places = [
            PlaceItem(
                id=f"PLC-FALLBACK-{i+1}",
                name=f"{dest_title} Landmark Experience #{i+1}",
                category="Sightseeing & Culture",
                estimated_cost=25.0,
                rating=4.7,
                address=dest_title,
                source="Rule-based Planner",
                is_mock=True
            )
            for i in range(trip_days * 2)
        ]

    place_index = 0
    time_slots = ["Morning", "Afternoon", "Evening"]

    for d in range(1, trip_days + 1):
        day_activities: List[ActivityOption] = []
        theme = DEFAULT_THEMES[(d - 1) % len(DEFAULT_THEMES)]

        # Schedule 2 to 3 activities per day
        slots_for_day = time_slots[:2] if d == 1 or d == trip_days else time_slots

        for slot in slots_for_day:
            if place_index < len(candidate_places):
                p = candidate_places[place_index]
                place_index += 1
            else:
                # Wrap around candidate places
                p = candidate_places[(place_index) % len(candidate_places)]
                place_index += 1

            cost = p.estimated_cost if p.estimated_cost is not None else 25.0
            # Scale cost to fit reasonably within per_day_budget
            max_slot_cost = max(10.0, per_day_budget * 0.45)
            adjusted_cost = min(cost, max_slot_cost)

            day_activities.append(ActivityOption(
                id=f"ACT-D{d}-{p.id}",
                name=p.name,
                category=p.category,
                estimated_cost=round(adjusted_cost, 2),
                currency="USD",
                day=d,
                time_slot=slot,
                duration="2-3 hours",
                rating=p.rating or 4.7,
                description=p.description or f"Enjoy visiting {p.name} in {dest_title}.",
                address=p.address or dest_title,
                coordinates=p.coordinates,
                source=p.source,
                is_mock=p.is_mock
            ))

        daily_total = round(sum(a.estimated_cost for a in day_activities), 2)
        days.append(DayPlan(
            day=d,
            theme=theme,
            estimated_daily_cost=daily_total,
            activities=day_activities
        ))

    return DayByDayPlan(
        days=days,
        summary=f"Balanced {trip_days}-day itinerary across {dest_title} with {len(days)} structured days."
    )

def _clean_json_response(raw_text: str) -> str:
    """Removes markdown code block formatting to extract raw JSON."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def _call_gemini_with_retry(api_key: str, model: str, prompt: str) -> str:
    """Calls Google Gemini API generateContent endpoint with 503/429 exponential backoff retries."""
    cleaned_model = model.strip()
    if cleaned_model.startswith("models/"):
        cleaned_model = cleaned_model[7:]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cleaned_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }
    with httpx.Client(timeout=20.0) as client:
        for retry_idx in range(len(BACKOFF_DELAYS) + 1):
            resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini returned zero response candidates")
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text

            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message") or err_msg
            except Exception:
                pass

            # Exponential backoff specifically for 503 (High Demand / Overloaded) and 429 (Rate Limit)
            if resp.status_code in (503, 429) and retry_idx < len(BACKOFF_DELAYS):
                wait_sec = BACKOFF_DELAYS[retry_idx]
                logger.warning(
                    f"Gemini call ({cleaned_model}) encountered HTTP {resp.status_code} ({err_msg}). "
                    f"Retrying with exponential backoff in {wait_sec}s (retry {retry_idx + 1}/{len(BACKOFF_DELAYS)})..."
                )
                time.sleep(wait_sec)
                continue

            raise RuntimeError(f"HTTP status {resp.status_code}: {err_msg}")

def _call_openai_with_retry(api_key: str, model: str, prompt: str) -> str:
    """Calls OpenAI-compatible chat/completions endpoint with 503/429 exponential backoff retries."""
    url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional travel planning AI. Return only valid JSON adhering strictly to the requested schema."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    with httpx.Client(timeout=20.0) as client:
        for retry_idx in range(len(BACKOFF_DELAYS) + 1):
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("OpenAI returned zero response choices")
                return choices[0].get("message", {}).get("content", "")

            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message") or err_msg
            except Exception:
                pass

            if resp.status_code in (503, 429) and retry_idx < len(BACKOFF_DELAYS):
                wait_sec = BACKOFF_DELAYS[retry_idx]
                logger.warning(
                    f"OpenAI call ({model}) encountered HTTP {resp.status_code} ({err_msg}). "
                    f"Retrying with exponential backoff in {wait_sec}s (retry {retry_idx + 1}/{len(BACKOFF_DELAYS)})..."
                )
                time.sleep(wait_sec)
                continue

            raise RuntimeError(f"HTTP status {resp.status_code}: {err_msg}")

def plan_day_by_day_activities(
    candidate_places: List[PlaceItem],
    trip_days: int,
    destination: str,
    preferences: str,
    per_day_budget: float,
    model: Optional[str] = None,
    fallback_model: Optional[str] = None
) -> Tuple[DayByDayPlan, bool, Optional[str], Optional[str]]:
    """
    Coordinates planning of day-by-day activities:
    1. Reads primary model from LLM_MODEL (default: gemini-2.5-flash / gpt-4o-mini).
    2. Reads fallback model from LLM_FALLBACK_MODEL (default: gemini-3.1-flash-lite / gpt-4o-mini).
    3. Executes requests with 503/429 exponential backoff (2s, 5s, 10s).
    4. If the primary model fails (e.g. repeated 503s), falls back to trying LLM_FALLBACK_MODEL.
    5. Validates output with DayByDayPlan Pydantic model.
    6. If all models in the chain fail, falls back to rule-based distribution.
    Returns: (DayByDayPlan, used_llm: bool, fallback_reason: Optional[str], actual_model: Optional[str])
    """
    llm_key = os.getenv("LLM_API_KEY", "").strip()
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    primary_default = "gemini-2.5-flash" if llm_provider == "gemini" else "gpt-4o-mini"
    primary_model = (model or os.getenv("LLM_MODEL") or "").strip() or primary_default
    if primary_model.startswith("models/"):
        primary_model = primary_model[7:]

    fallback_default = "gemini-3.1-flash-lite" if llm_provider == "gemini" else "gpt-4o-mini"
    resolved_fallback = (fallback_model or os.getenv("LLM_FALLBACK_MODEL") or "").strip() or fallback_default
    if resolved_fallback.startswith("models/"):
        resolved_fallback = resolved_fallback[7:]

    # Fallback immediately if key is missing or placeholder
    if not llm_key or llm_key == "your_llm_api_key_here":
        reason = "Missing LLM_API_KEY environment variable"
        logger.info(f"{reason}; executing rule-based day-by-day planner.")
        rule_plan = create_rule_based_plan(candidate_places, trip_days, destination, per_day_budget)
        return rule_plan, False, reason, None

    # Construct model chain: primary model first, fallback model second if distinct
    model_chain: List[str] = [primary_model]
    if resolved_fallback and resolved_fallback != primary_model:
        model_chain.append(resolved_fallback)

    # Prepare places context for LLM prompt
    places_summary = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "address": p.address,
            "rating": p.rating,
            "estimated_cost": p.estimated_cost,
            "description": p.description,
            "coordinates": p.coordinates
        }
        for p in candidate_places
    ]

    prompt = f"""
You are an expert travel planner. Create a detailed day-by-day itinerary plan for a {trip_days}-day trip to {destination}.

TRAVEL DETAILS:
- Destination: {destination}
- Duration: {trip_days} days (Day 1 through Day {trip_days})
- Traveler Preferences: {preferences or 'Top city attractions, culture, culinary highlights'}
- Target Activity Budget Per Day: ${per_day_budget:.2f} USD

CANDIDATE PLACES TO SELECT FROM:
{json.dumps(places_summary, indent=2)}

INSTRUCTIONS:
1. Construct a schedule for exactly {trip_days} days.
2. For each day, provide:
   - "day": integer (1 to {trip_days})
   - "theme": a descriptive title for that day's focus (e.g. "Historic Quarter & Art Exploration")
   - "estimated_daily_cost": float total cost of that day's activities
   - "activities": an array of 2 to 3 activities for that day
3. For each activity, include:
   - "id": unique string ID
   - "name": string
   - "category": string (e.g. "Museum & Art", "Food & Culinary", "Sightseeing & Culture", "Park & Nature")
   - "estimated_cost": float
   - "currency": "USD"
   - "day": integer matching the parent day
   - "time_slot": "Morning", "Afternoon", or "Evening"
   - "duration": string (e.g. "2 hours")
   - "rating": float
   - "description": string explaining why to visit
   - "address": string address if known
   - "coordinates": {{"latitude": float, "longitude": float}} if known
4. Return ONLY valid JSON adhering to this JSON schema:
{{
  "days": [
    {{
      "day": 1,
      "theme": "...",
      "estimated_daily_cost": 45.0,
      "activities": [ ... ]
    }}
  ],
  "summary": "..."
}}
"""

    chain_errors: List[str] = []

    for chain_idx, current_model in enumerate(model_chain):
        is_fallback_attempt = (chain_idx > 0)
        if is_fallback_attempt:
            logger.info(f"Model chain fallback: attempting secondary model '{current_model}'...")

        last_error_for_model: Optional[str] = None

        # Attempt call (up to 2 tries: initial + 1 schema retry on invalid output)
        for attempt in range(2):
            try:
                logger.info(
                    f"Calling LLM planner ({llm_provider}/{current_model}), "
                    f"chain step {chain_idx + 1}/{len(model_chain)}, attempt {attempt + 1}..."
                )
                if llm_provider == "openai":
                    raw_response = _call_openai_with_retry(llm_key, current_model, prompt)
                else:
                    raw_response = _call_gemini_with_retry(llm_key, current_model, prompt)

                cleaned_json = _clean_json_response(raw_response)
                parsed_dict = json.loads(cleaned_json)

                # Validate against Pydantic DayByDayPlan model
                validated_plan = DayByDayPlan.model_validate(parsed_dict)
                if validated_plan.days and len(validated_plan.days) > 0:
                    logger.info(
                        f"Successfully generated and validated {len(validated_plan.days)}-day plan "
                        f"via LLM using model '{current_model}'."
                    )
                    return validated_plan, True, None, current_model
                else:
                    raise ValueError("Plan contains zero scheduled days")
            except Exception as e:
                last_error_for_model = str(e)
                logger.warning(
                    f"LLM planner attempt {attempt + 1} for model '{current_model}' failed: {last_error_for_model}"
                )
                # If error is an HTTP/API or connection error, the model endpoint itself is failing.
                # Skip secondary schema retry to fail fast and immediately advance to fallback model.
                if (
                    "HTTP status" in last_error_for_model
                    or "connect" in last_error_for_model.lower()
                    or "timeout" in last_error_for_model.lower()
                ):
                    logger.info(f"Skipping schema retry for '{current_model}' due to service-level failure.")
                    break

        chain_errors.append(f"{current_model}: {last_error_for_model}")

        if chain_idx < len(model_chain) - 1:
            next_model = model_chain[chain_idx + 1]
            logger.warning(
                f"Model '{current_model}' failed after retries. Falling back to next model in chain: '{next_model}'..."
            )

    # Fallback to rule-based planner after all models in chain failed
    fallback_reason = f"LLM planning failed across model chain ({'; '.join(chain_errors)})"
    logger.warning(f"{fallback_reason}; using rule-based planner fallback.")
    fallback_plan = create_rule_based_plan(candidate_places, trip_days, destination, per_day_budget)
    return fallback_plan, False, fallback_reason, None
