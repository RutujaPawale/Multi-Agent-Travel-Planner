import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .state import TravelPlanState

try:
    from providers import get_flight_provider, MockProvider, FlightOption
except (ImportError, ModuleNotFoundError):
    from agent_service.providers import get_flight_provider, MockProvider, FlightOption

try:
    from db import log_agent_run
except (ImportError, ModuleNotFoundError):
    from agent_service.db import log_agent_run

logger = logging.getLogger("flight_agent")

def flight_agent_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Flight Agent Node:
    Queries configured FlightProvider (Duffel API or MockProvider).
    Selects provider via FLIGHT_PROVIDER (duffel | mock), defaulting to mock if DUFFEL_API_KEY is missing.
    Ranks top 3 flight options by price.
    On any fallback (missing key, HTTP status error, or exception), logs the reason
    to PostgreSQL agent_runs.error_message.
    """
    trip_id = state.get("trip_id")
    origin = state.get("origin", "JFK")
    destination = state.get("destination", "CDG")
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    budget = float(state.get("budget", 1000.0))

    input_payload = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "budget": budget
    }

    # Select provider through factory
    provider, is_fallback, fallback_reason = get_flight_provider()
    provider_name = type(provider).__name__
    error_msg: Optional[str] = fallback_reason
    flights: List[Dict[str, Any]] = []

    if not is_fallback:
        try:
            logger.info(f"Attempting live flight search via {provider_name} for {origin} -> {destination}...")
            flight_models: List[FlightOption] = provider.search_flights(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget
            )
            if flight_models:
                flights = [f.model_dump() for f in flight_models]
                is_fallback = False
                error_msg = None
            else:
                fallback_reason = "Duffel Flights API returned 0 offers for route/dates"
                logger.warning(f"{fallback_reason}; falling back to MockProvider.")
                is_fallback = True
                error_msg = fallback_reason
                fallback_models = MockProvider().search_flights(origin, destination, start_date, end_date, budget)
                flights = [f.model_dump() for f in fallback_models]
        except Exception as e:
            fallback_reason = str(e)
            logger.warning(f"{provider_name} flight search failed ({fallback_reason}); falling back to MockProvider.")
            is_fallback = True
            error_msg = fallback_reason
            fallback_models = MockProvider().search_flights(origin, destination, start_date, end_date, budget)
            flights = [f.model_dump() for f in fallback_models]
    else:
        logger.info(f"Using MockProvider for flights ({fallback_reason}).")
        flight_models = provider.search_flights(
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget
        )
        flights = [f.model_dump() for f in flight_models]

    active_provider = "MockProvider" if is_fallback else provider_name
    status = "SUCCESS"

    output_payload = {
        "flight_count": len(flights),
        "top_flights": flights,
        "provider": active_provider,
        "used_live_api": not is_fallback,
        "is_fallback": is_fallback,
        "fallback_reason": error_msg,
        "error_notice": error_msg
    }

    # Persist log to PostgreSQL agent_runs table with error_message on fallback
    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Flight Agent",
        input_data=input_payload,
        output_data=output_payload,
        status=status,
        error_message=error_msg
    )

    log_entry = {
        "agent": "Flight Agent",
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": f"Found {len(flights)} flight options ranked by price (Provider: {active_provider}).",
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "flight_options": flights,
        "agent_logs": agent_logs
    }
