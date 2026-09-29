from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

class TravelPlanState(TypedDict, total=False):
    trip_id: Optional[str]
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget: float
    preferences: Optional[str]
    flight_options: List[Dict[str, Any]]
    hotel_options: List[Dict[str, Any]]
    activity_options: List[Dict[str, Any]]
    budget_summary: Dict[str, Any]
    final_itinerary: Dict[str, Any]
    errors: List[str]
    agent_logs: List[Dict[str, Any]]
    orchestrator_run_id: Optional[str]
