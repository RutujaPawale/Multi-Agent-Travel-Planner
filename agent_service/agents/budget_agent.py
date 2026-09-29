import logging
from datetime import datetime
from typing import Any, Dict
from .state import TravelPlanState
try:
    from db import log_agent_run
except (ImportError, ModuleNotFoundError):
    from agent_service.db import log_agent_run

logger = logging.getLogger("budget_agent")

def budget_agent_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Budget Agent (Stub):
    Analyzes total trip budget versus projected expenses (cheapest flight + mid-tier hotel + activities).
    Logs execution to PostgreSQL agent_runs table.
    """
    trip_id = state.get("trip_id")
    total_budget = float(state.get("budget", 1000.0))
    start_date_str = state.get("start_date", "")
    end_date_str = state.get("end_date", "")

    # Calculate trip duration in nights
    nights = 4
    try:
        if start_date_str and end_date_str:
            d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
            d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
            diff = (d2 - d1).days
            if diff > 0:
                nights = diff
    except Exception as e:
        logger.warning(f"Could not calculate dates difference: {e}")

    # Estimate component costs
    flights = state.get("flight_options", [])
    cheapest_flight_cost = float(flights[0]["price"]) if flights else 350.0

    hotels = state.get("hotel_options", [])
    # Top-ranked hotel recommendation (by rating and price)
    selected_hotel = hotels[0] if hotels else None
    if selected_hotel and "total_price" in selected_hotel:
        total_hotel_cost = round(float(selected_hotel["total_price"]), 2)
        hotel_rate = round(float(selected_hotel.get("price_per_night", total_hotel_cost / nights)), 2)
    elif selected_hotel and "price_per_night" in selected_hotel:
        hotel_rate = float(selected_hotel["price_per_night"])
        total_hotel_cost = round(hotel_rate * nights, 2)
    else:
        hotel_rate = 140.0
        total_hotel_cost = round(hotel_rate * nights, 2)

    activities = state.get("activity_options", [])
    total_activity_cost = round(sum(float(a.get("estimated_cost", 0.0)) for a in activities), 2)

    # Miscellaneous buffer (meals, local transport, tips ~ 20%)
    miscellaneous = round((total_hotel_cost + total_activity_cost) * 0.25, 2)

    total_estimated_expense = round(cheapest_flight_cost + total_hotel_cost + total_activity_cost + miscellaneous, 2)
    remaining_budget = round(total_budget - total_estimated_expense, 2)

    if remaining_budget >= 0:
        status_eval = "Within Budget"
        recommendation = "Trip plan is well within allocated funds. Extra budget can be used for fine dining or upgrades."
    elif abs(remaining_budget) <= total_budget * 0.15:
        status_eval = "Slightly Over Budget"
        recommendation = "Consider opting for budget accommodation or selecting fewer premium tours to stay on budget."
    else:
        status_eval = "Exceeds Budget"
        recommendation = "Estimated costs exceed target budget. Consider adjusting travel dates or selecting economy options."

    budget_breakdown = {
        "user_target_budget": total_budget,
        "trip_duration_nights": nights,
        "estimated_flight_cost": cheapest_flight_cost,
        "estimated_hotel_cost": total_hotel_cost,
        "estimated_activities_cost": total_activity_cost,
        "estimated_miscellaneous": miscellaneous,
        "total_estimated_expense": total_estimated_expense,
        "remaining_surplus_deficit": remaining_budget,
        "budget_health": status_eval,
        "recommendation": recommendation,
        "currency": "USD"
    }

    input_payload = {
        "budget": total_budget,
        "nights": nights,
        "flight_cost": cheapest_flight_cost,
        "hotel_rate": hotel_rate
    }

    output_payload = {
        "status": "STUB_DATA",
        "breakdown": budget_breakdown
    }

    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Budget Agent",
        input_data=input_payload,
        output_data=output_payload,
        status="SUCCESS"
    )

    log_entry = {
        "agent": "Budget Agent",
        "status": "SUCCESS (Stub)",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": f"Calculated budget feasibility: {status_eval} (Est: ${total_estimated_expense} vs Budget: ${total_budget}).",
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "budget_summary": budget_breakdown,
        "agent_logs": agent_logs
    }
