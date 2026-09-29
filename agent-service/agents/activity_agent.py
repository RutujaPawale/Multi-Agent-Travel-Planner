import logging
from datetime import datetime
from typing import Any, Dict, List
from .state import TravelPlanState
try:
    from db import log_agent_run
except (ImportError, ModuleNotFoundError):
    from agent_service.db import log_agent_run

logger = logging.getLogger("activity_agent")

def activity_agent_node(state: TravelPlanState) -> Dict[str, Any]:
    """
    Activity Agent (Stub):
    Returns 3 realistic placeholder activities/tours for the destination.
    Logs execution to PostgreSQL agent_runs table.
    """
    trip_id = state.get("trip_id")
    destination = state.get("destination", "Destination")
    preferences = state.get("preferences", "")

    input_payload = {
        "destination": destination,
        "preferences": preferences
    }

    # Hardcoded placeholder activities (stub logic)
    placeholder_activities = [
        {
            "rank": 1,
            "id": "ACT-001",
            "name": f"Historic Walking Tour & Hidden Gems of {destination}",
            "category": "Culture & Heritage",
            "estimated_cost": 45.0,
            "currency": "USD",
            "duration": "3 hours",
            "rating": 4.9,
            "description": "Guided walking tour through historic quarters with a local historian, including coffee tastings."
        },
        {
            "rank": 2,
            "id": "ACT-002",
            "name": f"Iconic Landmarks & Panoramic Viewpoints Excursion",
            "category": "Sightseeing",
            "estimated_cost": 65.0,
            "currency": "USD",
            "duration": "4 hours",
            "rating": 4.7,
            "description": "Skip-the-line access to major architectural monuments and observation decks."
        },
        {
            "rank": 3,
            "id": "ACT-003",
            "name": f"Culinary Tasting Tour & Night Market Adventure",
            "category": "Food & Drink",
            "estimated_cost": 80.0,
            "currency": "USD",
            "duration": "3.5 hours",
            "rating": 4.85,
            "description": "Sample 6 local specialties, artisanal cheeses/pastries, and regional wine pairings."
        }
    ]

    output_payload = {
        "status": "STUB_DATA",
        "activity_count": len(placeholder_activities),
        "activities": placeholder_activities
    }

    log_id = log_agent_run(
        trip_id=trip_id,
        agent_name="Activity Agent",
        input_data=input_payload,
        output_data=output_payload,
        status="SUCCESS"
    )

    log_entry = {
        "agent": "Activity Agent",
        "status": "SUCCESS (Stub)",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": f"Selected {len(placeholder_activities)} curated activities and tours (placeholder).",
        "log_id": log_id,
        "details": output_payload
    }

    agent_logs = list(state.get("agent_logs", []))
    agent_logs.append(log_entry)

    return {
        "activity_options": placeholder_activities,
        "agent_logs": agent_logs
    }
