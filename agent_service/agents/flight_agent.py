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

try:
    from broadcaster import publish_trip_event
except (ImportError, ModuleNotFoundError):
    try:
        from agent_service.broadcaster import publish_trip_event
    except (ImportError, ModuleNotFoundError):
        publish_trip_event = None

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
    # Check if budget agent provided a reduced flight_budget_cap during re-planning
    replan_cap = state.get("flight_budget_cap")
    if replan_cap is not None:
        flight_budget = round(float(replan_cap), 2)
        logger.info(f"Flight Agent applying re-planning flight budget cap: ${flight_budget:.2f}")
        start_msg = f"Re-evaluating flight options with reduced budget cap ${flight_budget:.2f}..."
    else:
        flight_budget = float(state.get("budget", 1000.0))
        start_msg = f"Searching flights for {origin} -> {destination}..."

    if publish_trip_event and trip_id:
        publish_trip_event(
            trip_id=str(trip_id),
            agent="Flight Agent",
            status="STARTED",
            message=start_msg,
            details={"origin": origin, "destination": destination, "budget": flight_budget}
        )

    input_payload = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "budget": flight_budget,
        "replan_cap_applied": replan_cap is not None,
        "replan_attempt": state.get("replan_count", 0)
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
                budget=flight_budget
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
                fallback_models = MockProvider().search_flights(origin, destination, start_date, end_date, flight_budget)
                flights = [f.model_dump() for f in fallback_models]
        except Exception as e:
            fallback_reason = str(e)
            logger.warning(f"{provider_name} flight search failed ({fallback_reason}); falling back to MockProvider.")
            is_fallback = True
            error_msg = fallback_reason
            fallback_models = MockProvider().search_flights(origin, destination, start_date, end_date, flight_budget)
            flights = [f.model_dump() for f in fallback_models]
    else:
        logger.info(f"Using MockProvider for flights ({fallback_reason}).")
        flight_models = provider.search_flights(
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=flight_budget
        )
        flights = [f.model_dump() for f in flight_models]

    active_provider = "MockProvider" if is_fallback else provider_name
    status = "SUCCESS"

    # Evaluate filter mode against budget cap
    filter_mode: Optional[str] = None
    filter_message: Optional[str] = None
    if flight_budget > 0 and flights:
        qualifying = [f for f in flights if f.get("price", 0.0) <= flight_budget]
        if qualifying:
            filter_mode = "QUALIFYING_UNDER_CAP"
            filter_message = f"Found {len(qualifying)} offer(s) qualifying at or under budget cap (${flight_budget:.2f}); selected top {len(flights)} option(s)."
            logger.info(f"Flight Agent selection mode: {filter_mode} - {filter_message}")
        else:
            lowest_price = min(f.get("price", 0.0) for f in flights)
            filter_mode = "FALLBACK_CHEAPEST_AVAILABLE"
            filter_message = f"No flight offers found at or under cap (${flight_budget:.2f}). Fell back to cheapest available offers (lowest: ${lowest_price:.2f})."
            logger.warning(f"Flight Agent selection mode: {filter_mode} - {filter_message}")

    output_payload = {
        "flight_count": len(flights),
        "top_flights": flights,
        "flight_budget": flight_budget,
        "flight_budget_cap": replan_cap,
        "filter_mode": filter_mode,
        "filter_message": filter_message,
        "provider": active_provider,
        "used_live_api": not is_fallback,
        "is_fallback": is_fallback,
        "replan_cap_applied": replan_cap is not None,
        "replan_attempt": state.get("replan_count", 0),
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

    summary_text = f"Found {len(flights)} flight options ranked by price (Provider: {active_provider})."
    if filter_mode:
        summary_text += f" [{filter_mode}: {filter_message}]"

    log_entry = {
        "agent": "Flight Agent",
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": summary_text,
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "flight_options": flights,
        "agent_logs": agent_logs
    }
