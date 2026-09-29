import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .state import TravelPlanState

try:
    from providers import get_hotel_provider, MockProvider, HotelOption
except (ImportError, ModuleNotFoundError):
    from agent_service.providers import get_hotel_provider, MockProvider, HotelOption

try:
    from db import log_agent_run
except (ImportError, ModuleNotFoundError):
    from agent_service.db import log_agent_run

logger = logging.getLogger("hotel_agent")

def calculate_stay_nights(start_date_str: str, end_date_str: str) -> int:
    """Calculates number of nights between start_date and end_date (minimum 1)."""
    try:
        if start_date_str and end_date_str:
            d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
            d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
            diff = (d2 - d1).days
            return max(1, diff)
    except Exception as e:
        logger.warning(f"Could not calculate dates difference for hotel stay: {e}")
    return 4

def hotel_agent_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Hotel Agent Node:
    Queries configured HotelProvider (Duffel API or MockProvider).
    Selects provider via HOTEL_PROVIDER (duffel | mock), defaulting to mock if DUFFEL_API_KEY is missing.
    Allocates configurable % of budget to lodging (default 35%, HOTEL_BUDGET_PCT env var)
    and filters by resulting per-night cap.
    Ranks by rating (descending), then price (ascending); returns top 3 hotel options.
    On any fallback (missing key, HTTP status error, or exception), logs the reason
    to PostgreSQL agent_runs.error_message.
    """
    trip_id = state.get("trip_id")
    destination = state.get("destination", "Paris")
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    total_budget = float(state.get("budget", 2000.0))

    # Configuration: Hotel budget percentage
    hotel_budget_pct_str = os.getenv("HOTEL_BUDGET_PCT", "35.0")
    try:
        hotel_budget_pct = float(hotel_budget_pct_str)
    except ValueError:
        hotel_budget_pct = 35.0

    nights = calculate_stay_nights(start_date, end_date)
    lodging_budget = round(total_budget * (hotel_budget_pct / 100.0), 2)
    per_night_cap = round(lodging_budget / nights, 2)

    input_payload = {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "total_budget": total_budget,
        "hotel_budget_pct": hotel_budget_pct,
        "lodging_budget": lodging_budget,
        "nights": nights,
        "per_night_cap": per_night_cap,
        "preferences": state.get("preferences", "")
    }

    # Select provider through factory
    provider, is_fallback, fallback_reason = get_hotel_provider()
    provider_name = type(provider).__name__
    error_msg: Optional[str] = fallback_reason
    hotels: List[Dict[str, Any]] = []

    if not is_fallback:
        try:
            logger.info(f"Attempting live hotel search via {provider_name} for {destination}...")
            hotel_models: List[HotelOption] = provider.search_hotels(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=total_budget,
                per_night_cap=per_night_cap,
                nights=nights
            )
            if hotel_models:
                hotels = [h.model_dump() for h in hotel_models]
                is_fallback = False
                error_msg = None
            else:
                fallback_reason = "Duffel Stays API returned 0 properties for destination"
                logger.warning(f"{fallback_reason}; falling back to MockProvider.")
                is_fallback = True
                error_msg = fallback_reason
                fallback_models = MockProvider().search_hotels(
                    destination=destination,
                    start_date=start_date,
                    end_date=end_date,
                    budget=total_budget,
                    per_night_cap=per_night_cap,
                    nights=nights
                )
                hotels = [h.model_dump() for h in fallback_models]
        except Exception as e:
            fallback_reason = str(e)
            logger.warning(f"{provider_name} hotel search failed ({fallback_reason}); falling back to MockProvider.")
            is_fallback = True
            error_msg = fallback_reason
            fallback_models = MockProvider().search_hotels(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=total_budget,
                per_night_cap=per_night_cap,
                nights=nights
            )
            hotels = [h.model_dump() for h in fallback_models]
    else:
        logger.info(f"Using MockProvider for hotels ({fallback_reason}).")
        hotel_models = provider.search_hotels(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=total_budget,
            per_night_cap=per_night_cap,
            nights=nights
        )
        hotels = [h.model_dump() for h in hotel_models]

    active_provider = "MockProvider" if is_fallback else provider_name
    status = "SUCCESS"

    output_payload = {
        "hotel_count": len(hotels),
        "top_hotels": hotels,
        "per_night_cap": per_night_cap,
        "lodging_budget": lodging_budget,
        "nights": nights,
        "provider": active_provider,
        "used_live_api": not is_fallback,
        "is_fallback": is_fallback,
        "fallback_reason": error_msg,
        "error_notice": error_msg
    }

    # Persist log to PostgreSQL agent_runs table with error_message on fallback
    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Hotel Agent",
        input_data=input_payload,
        output_data=output_payload,
        status=status,
        error_message=error_msg
    )

    log_entry = {
        "agent": "Hotel Agent",
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": f"Selected top {len(hotels)} hotels ranked by rating & price (Cap: ${per_night_cap}/night, Provider: {active_provider}).",
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "hotel_options": hotels,
        "agent_logs": agent_logs
    }
