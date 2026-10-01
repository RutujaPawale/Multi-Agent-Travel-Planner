import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .state import TravelPlanState
from .llm_planner import plan_day_by_day_activities

try:
    from providers import get_places_provider, MockProvider, PlaceItem, ActivityOption, DayPlan, DayByDayPlan
except (ImportError, ModuleNotFoundError):
    from agent_service.providers import get_places_provider, MockProvider, PlaceItem, ActivityOption, DayPlan, DayByDayPlan

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

logger = logging.getLogger("activity_agent")

def calculate_trip_days(start_date_str: str, end_date_str: str) -> int:
    """Calculates number of trip days between start_date and end_date (minimum 1)."""
    try:
        if start_date_str and end_date_str:
            d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
            d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
            diff = (d2 - d1).days
            return max(1, diff)
    except Exception as e:
        logger.warning(f"Could not calculate dates difference for activities: {e}")
    return 4

def activity_agent_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Activity Agent Node:
    1. Data source: Fetches candidate attractions, restaurants, and POIs via PlacesProvider
       (OpenTripMap API /places/radius + /places/xid or MockProvider if key is missing/errors).
    2. Planning: Invokes LLM planner (via LLM_PROVIDER / LLM_API_KEY) with Pydantic JSON validation,
       retrying once on invalid schema, or falls back to rule-based day-by-day distribution.
    3. Allocates configurable share of total budget to activities (ACTIVITY_BUDGET_PCT, default 20%).
    4. Each activity includes name, category, estimated cost, address, coordinates, and day assignment.
    5. Logs execution, flags (is_mock, used_llm), and fallback error messages to PostgreSQL agent_runs.
    """
    trip_id = state.get("trip_id")
    destination = state.get("destination", "Paris")
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    total_budget = float(state.get("budget", 2000.0))
    preferences = state.get("preferences", "")

    trip_days = calculate_trip_days(start_date, end_date)

    # Check if budget agent provided a reduced activity_budget_cap during re-planning
    replan_cap = state.get("activity_budget_cap")
    activity_budget_pct_str = os.getenv("ACTIVITY_BUDGET_PCT", "20.0")
    try:
        activity_budget_pct = float(activity_budget_pct_str)
    except ValueError:
        activity_budget_pct = 20.0

    if replan_cap is not None:
        activity_budget = round(float(replan_cap), 2)
        logger.info(f"Activity Agent applying re-planning activity budget cap: ${activity_budget:.2f}")
        start_msg = f"Re-structuring activities with reduced budget cap ${activity_budget:.2f} (${round(activity_budget / max(1, trip_days), 2)}/day)..."
    else:
        activity_budget = round(total_budget * (activity_budget_pct / 100.0), 2)
        start_msg = f"Discovering attractions and planning daily itinerary for {destination} (${round(activity_budget / max(1, trip_days), 2)}/day budget)..."

    per_day_budget = round(activity_budget / max(1, trip_days), 2)

    if publish_trip_event and trip_id:
        publish_trip_event(
            trip_id=str(trip_id),
            agent="Activity Agent",
            status="STARTED",
            message=start_msg,
            details={"destination": destination, "activity_budget": activity_budget, "per_day_budget": per_day_budget, "trip_days": trip_days}
        )

    input_payload = {
        "destination": destination,
        "trip_days": trip_days,
        "start_date": start_date,
        "end_date": end_date,
        "total_budget": total_budget,
        "activity_budget_pct": activity_budget_pct,
        "activity_budget": activity_budget,
        "per_day_budget": per_day_budget,
        "replan_cap_applied": replan_cap is not None,
        "replan_attempt": state.get("replan_count", 0),
        "preferences": preferences
    }

    # Step 1: Fetch candidate places using configured PlacesProvider
    places_provider, is_places_fallback, places_fallback_reason = get_places_provider()
    places_provider_name = type(places_provider).__name__
    candidate_places: List[PlaceItem] = []

    if not is_places_fallback:
        try:
            logger.info(f"Fetching attractions via {places_provider_name} for {destination}...")
            candidate_places = places_provider.fetch_places(destination, preferences, limit=15)
            if not candidate_places:
                places_fallback_reason = "OpenTripMap API returned 0 results; using mock candidate places"
                logger.warning(places_fallback_reason)
                is_places_fallback = True
                candidate_places = MockProvider().fetch_places(destination, preferences, limit=15)
        except Exception as e:
            places_fallback_reason = str(e)
            logger.warning(f"OpenTripMap API fetch failed ({places_fallback_reason}); falling back to MockProvider.")
            is_places_fallback = True
            candidate_places = MockProvider().fetch_places(destination, preferences, limit=15)
    else:
        logger.info(f"Using MockProvider for candidate places ({places_fallback_reason}).")
        candidate_places = places_provider.fetch_places(destination, preferences, limit=15)

    # Step 2: Plan day-by-day activities using LLM (or rule-based fallback)
    day_by_day_plan, used_llm, llm_fallback_reason, actual_model = plan_day_by_day_activities(
        candidate_places=candidate_places,
        trip_days=trip_days,
        destination=destination,
        preferences=preferences,
        per_day_budget=per_day_budget
    )

    # Flatten activities for state and downstream components (e.g. Budget Agent)
    flattened_activities: List[Dict[str, Any]] = []
    for day_plan in day_by_day_plan.days:
        for act in day_plan.activities:
            act_dict = act.model_dump()
            act_dict["rank"] = len(flattened_activities) + 1
            flattened_activities.append(act_dict)

    day_plans_dump = [d.model_dump() for d in day_by_day_plan.days]

    # Consolidate fallback notices
    fallback_reasons: List[str] = []
    if is_places_fallback and places_fallback_reason:
        fallback_reasons.append(f"Places: {places_fallback_reason}")
    if not used_llm and llm_fallback_reason:
        fallback_reasons.append(f"Planner: {llm_fallback_reason}")

    combined_error_msg: Optional[str] = "; ".join(fallback_reasons) if fallback_reasons else None
    active_places_provider = "MockProvider" if is_places_fallback else places_provider_name
    planner_mode = "LLM (AI Planner)" if used_llm else "Rule-based Planner"
    primary_model = (os.getenv("LLM_MODEL") or "").strip() or "gemini-2.5-flash"
    fallback_model = (os.getenv("LLM_FALLBACK_MODEL") or "").strip() or "gemini-3.1-flash-lite"
    model_used = actual_model if used_llm else "Rule-based Planner"

    output_payload = {
        "activity_count": len(flattened_activities),
        "day_count": len(day_plans_dump),
        "days": day_plans_dump,
        "activities": flattened_activities,
        "summary": day_by_day_plan.summary,
        "places_provider": active_places_provider,
        "planner_mode": planner_mode,
        "llm_model": primary_model,
        "llm_fallback_model": fallback_model,
        "model_used": model_used,
        "actual_model": actual_model,
        "is_mock": is_places_fallback,
        "used_llm": used_llm,
        "used_live_places": not is_places_fallback,
        "activity_budget": activity_budget,
        "per_day_budget": per_day_budget,
        "replan_cap_applied": replan_cap is not None,
        "replan_attempt": state.get("replan_count", 0),
        "fallback_reason": combined_error_msg,
        "error_notice": combined_error_msg
    }

    status = "SUCCESS"

    # Persist log to PostgreSQL agent_runs table
    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Activity Agent",
        input_data=input_payload,
        output_data=output_payload,
        status=status,
        error_message=combined_error_msg
    )

    log_entry = {
        "agent": "Activity Agent",
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": f"Planned {len(flattened_activities)} activities across {len(day_plans_dump)} days (Places: {active_places_provider}, Planner: {planner_mode} [{model_used}]).",
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "activity_options": flattened_activities,
        "day_plans": day_plans_dump,
        "agent_logs": agent_logs
    }
