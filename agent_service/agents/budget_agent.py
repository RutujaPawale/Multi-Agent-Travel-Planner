import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from .state import TravelPlanState

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

logger = logging.getLogger("budget_agent")

def calculate_stay_nights(start_date_str: str, end_date_str: str) -> int:
    """Calculates number of nights between start_date and end_date (minimum 1)."""
    try:
        if start_date_str and end_date_str:
            d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
            d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
            diff = (d2 - d1).days
            if diff > 0:
                return diff
    except Exception as e:
        logger.warning(f"Could not calculate dates difference for budget analysis: {e}")
    return 4

def budget_agent_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Budget Agent Node:
    1. Sums total estimated cost across Flight, Hotel, and Activity agents.
    2. Compares total cost against the user's target budget.
    3. If total exceeds budget and retry count < 2:
       - Identifies the largest overage source (hotel, flight, or activity).
       - Triggers a re-query to that agent with a 20% lower budget cap.
       - Logs the re-planning decision to PostgreSQL agent_runs with a clear 'reason' field.
    4. If within budget or max retries (2) reached:
       - Finalizes the budget breakdown (flights/hotel/activities/total vs budget).
       - Logs the final approval/summary to agent_runs.
       - Directs workflow to the synthesizer node.
    """
    trip_id = state.get("trip_id")
    user_budget = float(state.get("budget", 2000.0))
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    nights = calculate_stay_nights(start_date, end_date)

    # Re-planning state tracking
    replan_count = state.get("replan_count", 0)
    replan_reasons: List[str] = list(state.get("replan_reasons", []))

    if publish_trip_event and trip_id:
        publish_trip_event(
            trip_id=str(trip_id),
            agent="Budget Agent",
            status="STARTED",
            message=f"Auditing total estimated expenses against user budget (${user_budget:,.2f}) - Check {replan_count + 1}...",
            details={"user_budget": user_budget, "replan_attempt": replan_count}
        )

    # 1. Calculate Component Costs
    # Flights: top recommendation price
    flights = state.get("flight_options", [])
    if flights and isinstance(flights[0], dict) and "price" in flights[0]:
        flight_cost = round(float(flights[0]["price"]), 2)
    else:
        flight_cost = 0.0

    # Hotels: top recommendation total price (or price_per_night * nights)
    hotels = state.get("hotel_options", [])
    hotel_cost = 0.0
    if hotels and isinstance(hotels[0], dict):
        selected_hotel = hotels[0]
        if "total_price" in selected_hotel and selected_hotel["total_price"] is not None:
            hotel_cost = round(float(selected_hotel["total_price"]), 2)
        elif "price_per_night" in selected_hotel and selected_hotel["price_per_night"] is not None:
            hotel_cost = round(float(selected_hotel["price_per_night"]) * nights, 2)

    # Activities: sum of scheduled activity costs
    activities = state.get("activity_options", [])
    activity_cost = round(sum(float(a.get("estimated_cost", 0.0)) for a in activities), 2)

    # Total estimated cost
    total_estimated_cost = round(flight_cost + hotel_cost + activity_cost, 2)
    remaining_budget = round(user_budget - total_estimated_cost, 2)
    overage = round(total_estimated_cost - user_budget, 2)
    is_over_budget = overage > 0.0

    # 2. Calculate baseline budget allocations
    hotel_budget_pct = float(os.getenv("HOTEL_BUDGET_PCT", "35.0"))
    activity_budget_pct = float(os.getenv("ACTIVITY_BUDGET_PCT", "20.0"))
    flight_budget_pct = max(10.0, 100.0 - hotel_budget_pct - activity_budget_pct)

    current_hotel_cap = state.get("hotel_budget_cap")
    if current_hotel_cap is None:
        current_hotel_cap = round(user_budget * (hotel_budget_pct / 100.0), 2)

    current_activity_cap = state.get("activity_budget_cap")
    if current_activity_cap is None:
        current_activity_cap = round(user_budget * (activity_budget_pct / 100.0), 2)

    current_flight_cap = state.get("flight_budget_cap")
    if current_flight_cap is None:
        current_flight_cap = round(user_budget * (flight_budget_pct / 100.0), 2)

    # Individual component overages relative to respective caps
    hotel_overage = round(hotel_cost - current_hotel_cap, 2)
    flight_overage = round(flight_cost - current_flight_cap, 2)
    activity_overage = round(activity_cost - current_activity_cap, 2)

    # Check whether re-planning should be triggered (cap at 2 retries)
    replan_needed = is_over_budget and (replan_count < 2)

    new_hotel_cap = current_hotel_cap
    new_flight_cap = current_flight_cap
    new_activity_cap = current_activity_cap
    target_agent: Optional[str] = None
    decision_reason: str = ""

    if replan_needed:
        # Identify the largest overage source
        overages = {
            "hotel_agent": hotel_overage,
            "flight_agent": flight_overage,
            "activity_agent": activity_overage
        }
        positive_overages = {k: v for k, v in overages.items() if v > 0}

        if positive_overages:
            target_agent = max(positive_overages, key=positive_overages.get)
            agent_overage_amt = positive_overages[target_agent]
        else:
            # Fallback if no single item exceeded its percentage cap but sum exceeds budget
            costs = {
                "hotel_agent": hotel_cost,
                "flight_agent": flight_cost,
                "activity_agent": activity_cost
            }
            target_agent = max(costs, key=costs.get)
            agent_overage_amt = overage

        # Reduce budget cap for target agent by 20%
        if target_agent == "hotel_agent":
            new_hotel_cap = round(current_hotel_cap * 0.80, 2)
            category_name = "hotel"
            decision_reason = f"hotel over budget by ${agent_overage_amt:.2f}, re-querying with 20% lower budget cap (${new_hotel_cap:.2f})"
        elif target_agent == "flight_agent":
            new_flight_cap = round(current_flight_cap * 0.80, 2)
            category_name = "flight"
            decision_reason = f"flight over budget by ${agent_overage_amt:.2f}, re-querying with 20% lower budget cap (${new_flight_cap:.2f})"
        else:
            new_activity_cap = round(current_activity_cap * 0.80, 2)
            category_name = "activities"
            decision_reason = f"activities over budget by ${agent_overage_amt:.2f}, re-querying with 20% lower budget cap (${new_activity_cap:.2f})"

        replan_reasons.append(decision_reason)
        logger.info(
            f"Budget Agent: Re-planning attempt {replan_count + 1}/2 triggered. "
            f"Reason: {decision_reason}"
        )
    else:
        if replan_count >= 2 and is_over_budget:
            decision_reason = (
                f"Completed maximum 2 re-planning attempts. Final estimated cost is ${total_estimated_cost:.2f} "
                f"vs budget ${user_budget:.2f} (remaining overage: ${overage:.2f})."
            )
        else:
            decision_reason = (
                f"Trip is within budget: total estimated cost ${total_estimated_cost:.2f} "
                f"vs budget ${user_budget:.2f} (surplus: ${user_budget - total_estimated_cost:.2f})."
            )
        logger.info(f"Budget Agent final evaluation: {decision_reason}")

    # Build standardized budget breakdown (flights/hotel/activities/total vs budget)
    budget_breakdown = {
        # Core breakdown
        "user_budget": user_budget,
        "flights_cost": flight_cost,
        "hotel_cost": hotel_cost,
        "activities_cost": activity_cost,
        "total_estimated_cost": total_estimated_cost,
        "remaining_budget": remaining_budget,
        "is_over_budget": is_over_budget,
        "overage_amount": max(0.0, overage),
        "replan_attempts_used": replan_count + (1 if replan_needed else 0),
        "replan_reasons": replan_reasons,
        "currency": "USD",
        "budget_health": "Within Budget" if not is_over_budget else ("Slightly Over Budget" if overage <= user_budget * 0.15 else "Exceeds Budget"),

        # Backward-compatible UI fields
        "user_target_budget": user_budget,
        "trip_duration_nights": nights,
        "estimated_flight_cost": flight_cost,
        "estimated_hotel_cost": hotel_cost,
        "estimated_activities_cost": activity_cost,
        "estimated_miscellaneous": 0.0,
        "total_estimated_expense": total_estimated_cost,
        "remaining_surplus_deficit": remaining_budget,
        "recommendation": decision_reason
    }

    input_payload = {
        "user_budget": user_budget,
        "flights_cost": flight_cost,
        "hotel_cost": hotel_cost,
        "activities_cost": activity_cost,
        "total_estimated_cost": total_estimated_cost,
        "overage": overage,
        "replan_count": replan_count
    }

    if replan_needed:
        output_payload = {
            "status": "REPLANNING",
            "reason": decision_reason,
            "target_agent": target_agent,
            "replan_attempt": replan_count + 1,
            "max_attempts": 2,
            "new_hotel_budget_cap": new_hotel_cap,
            "new_flight_budget_cap": new_flight_cap,
            "new_activity_budget_cap": new_activity_cap,
            "budget_breakdown": budget_breakdown
        }
        log_status = "REPLANNING"
        error_msg = decision_reason
    else:
        output_payload = {
            "status": "COMPLETED",
            "reason": decision_reason,
            "replan_attempts_used": replan_count,
            "budget_breakdown": budget_breakdown
        }
        log_status = "SUCCESS"
        error_msg = decision_reason if (is_over_budget and replan_count >= 2) else None

    # Persist log to PostgreSQL agent_runs table
    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Budget Agent",
        input_data=input_payload,
        output_data=output_payload,
        status=log_status,
        error_message=error_msg
    )

    log_entry = {
        "agent": "Budget Agent",
        "status": log_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": decision_reason,
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "budget_summary": budget_breakdown,
        "replan_count": replan_count + 1 if replan_needed else replan_count,
        "is_replanning": replan_needed,
        "next_agent_to_replan": target_agent if replan_needed else None,
        "replan_reasons": replan_reasons,
        "hotel_budget_cap": new_hotel_cap,
        "flight_budget_cap": new_flight_cap,
        "activity_budget_cap": new_activity_cap,
        "agent_logs": agent_logs
    }
