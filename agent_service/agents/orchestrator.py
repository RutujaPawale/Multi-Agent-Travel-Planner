import logging
from datetime import datetime
from typing import Any, Dict
from langgraph.graph import StateGraph, START, END

from .state import TravelPlanState
from .flight_agent import flight_agent_node
from .hotel_agent import hotel_agent_node
from .activity_agent import activity_agent_node
from .budget_agent import budget_agent_node
try:
    from db import log_agent_run, update_agent_run
except (ImportError, ModuleNotFoundError):
    from agent_service.db import log_agent_run, update_agent_run

logger = logging.getLogger("orchestrator")

def orchestrator_init_node(state: TravelPlanState) -> Dict[str, Any]:
    """Logs the initialization of the multi-agent trip planning orchestration."""
    trip_id = state.get("trip_id")
    input_payload = {
        "origin": state.get("origin"),
        "destination": state.get("destination"),
        "start_date": state.get("start_date"),
        "end_date": state.get("end_date"),
        "budget": state.get("budget"),
        "preferences": state.get("preferences")
    }

    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Orchestrator Agent",
        input_data=input_payload,
        output_data={"status": "INITIALIZED", "message": "Starting multi-agent workflow"},
        status="IN_PROGRESS"
    )

    log_entry = {
        "agent": "Orchestrator Agent",
        "status": "IN_PROGRESS",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": "Initiated multi-agent travel planning graph workflow.",
        "log_id": log_id,
        "details": input_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "agent_logs": agent_logs,
        "orchestrator_run_id": log_id,
        "errors": state.get("errors", [])
    }

def synthesizer_node(state: TravelPlanState) -> Dict[str, Any]:
    """Compiles all agent contributions into the final synthesized travel itinerary."""
    trip_id = state.get("trip_id")
    origin = state.get("origin", "")
    destination = state.get("destination", "")
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    budget = state.get("budget", 0.0)
    preferences = state.get("preferences", "")

    flights = state.get("flight_options", [])
    hotels = state.get("hotel_options", [])
    activities = state.get("activity_options", [])
    day_plans = state.get("day_plans", [])
    budget_summary = state.get("budget_summary", {})

    final_itinerary = {
        "title": f"Custom Trip Itinerary: {origin} to {destination}",
        "summary": f"A curated travel plan from {origin} to {destination} ({start_date} to {end_date}) with a target budget of ${budget:,.2f}.",
        "preferences_applied": preferences or "None specified",
        "flights": {
            "count": len(flights),
            "recommended": flights[0] if flights else None,
            "all_options": flights
        },
        "accommodation": {
            "count": len(hotels),
            "recommended": hotels[0] if hotels else None,
            "all_options": hotels
        },
        "activities": {
            "count": len(activities),
            "day_count": len(day_plans),
            "days": day_plans,
            "highlights": activities
        },
        "financial_overview": budget_summary,
        "budget_breakdown": budget_summary,
        "generation_timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Update existing Orchestrator Agent row from IN_PROGRESS to SUCCESS
    orchestrator_run_id = state.get("orchestrator_run_id")
    orchestrator_output = {
        "status": "COMPLETED",
        "itinerary_title": final_itinerary["title"],
        "summary": final_itinerary["summary"],
        "flights_count": len(flights),
        "hotels_count": len(hotels),
        "activities_count": len(activities),
        "days_planned": len(day_plans),
        "replan_attempts": state.get("replan_count", 0),
        "final_budget": budget_summary
    }

    if orchestrator_run_id:
        update_agent_run(
            run_id=orchestrator_run_id,
            output_data=orchestrator_output,
            status="SUCCESS"
        )
    else:
        log_agent_run(
            trip_id=trip_id,
            agent_name="Orchestrator Agent",
            input_data={"stage": "SYNTHESIS"},
            output_data=orchestrator_output,
            status="SUCCESS"
        )

    # Update orchestrator entry in agent_logs
    agent_logs = list(state.get("agent_logs", []))
    updated_logs = []
    for log_item in agent_logs:
        if log_item.get("agent") == "Orchestrator Agent" and log_item.get("status") == "IN_PROGRESS":
            updated_logs.append({
                "agent": "Orchestrator Agent",
                "status": "SUCCESS",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "summary": "Synthesized final multi-agent itinerary and budget projection.",
                "log_id": orchestrator_run_id,
                "details": orchestrator_output
            })
        else:
            updated_logs.append(log_item)

    return {
        "final_itinerary": final_itinerary,
        "agent_logs": updated_logs
    }

def route_after_flight(state: TravelPlanState) -> str:
    """Routes to budget_agent if executing a re-plan, else advances to hotel_agent."""
    if state.get("is_replanning"):
        return "budget_agent"
    return "hotel_agent"

def route_after_hotel(state: TravelPlanState) -> str:
    """Routes to budget_agent if executing a re-plan, else advances to activity_agent."""
    if state.get("is_replanning"):
        return "budget_agent"
    return "activity_agent"

def route_after_budget(state: TravelPlanState) -> str:
    """
    Evaluates budget re-planning decisions:
    - If budget agent triggered a re-plan (max 2 retries), routes to target agent.
    - Otherwise, routes to synthesizer for final compilation.
    """
    target = state.get("next_agent_to_replan")
    if target in ("flight_agent", "hotel_agent", "activity_agent"):
        return target
    return "synthesizer"

def create_travel_planner_graph():
    """Builds and compiles the LangGraph StateGraph orchestration pipeline with budget re-planning loop."""
    workflow = StateGraph(TravelPlanState)

    # Register graph nodes
    workflow.add_node("orchestrator_init", orchestrator_init_node)
    workflow.add_node("flight_agent", flight_agent_node)
    workflow.add_node("hotel_agent", hotel_agent_node)
    workflow.add_node("activity_agent", activity_agent_node)
    workflow.add_node("budget_agent", budget_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # Initial pipeline flow
    workflow.add_edge(START, "orchestrator_init")
    workflow.add_edge("orchestrator_init", "flight_agent")

    # Conditional routing from flight_agent
    workflow.add_conditional_edges(
        "flight_agent",
        route_after_flight,
        {
            "hotel_agent": "hotel_agent",
            "budget_agent": "budget_agent"
        }
    )

    # Conditional routing from hotel_agent
    workflow.add_conditional_edges(
        "hotel_agent",
        route_after_hotel,
        {
            "activity_agent": "activity_agent",
            "budget_agent": "budget_agent"
        }
    )

    # Activity agent always routes to budget_agent
    workflow.add_edge("activity_agent", "budget_agent")

    # Conditional re-planning routing from budget_agent (capped at 2 retries)
    workflow.add_conditional_edges(
        "budget_agent",
        route_after_budget,
        {
            "flight_agent": "flight_agent",
            "hotel_agent": "hotel_agent",
            "activity_agent": "activity_agent",
            "synthesizer": "synthesizer"
        }
    )

    workflow.add_edge("synthesizer", END)

    return workflow.compile()
