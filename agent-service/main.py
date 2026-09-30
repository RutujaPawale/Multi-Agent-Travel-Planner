import os
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents.orchestrator import create_travel_planner_graph
from agents.state import TravelPlanState

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agent-service")

app = FastAPI(
    title="Multi-Agent AI Travel Planner - Agent Service",
    description="LangGraph-powered orchestration engine for travel itinerary planning.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile LangGraph orchestrator
planner_graph = create_travel_planner_graph()

class TripPlanRequest(BaseModel):
    trip_id: Optional[str] = Field(None, description="Trip ID in database if initiated by api-service")
    origin: str = Field(..., example="JFK", description="Origin city or IATA code")
    destination: str = Field(..., example="CDG", description="Destination city or IATA code")
    start_date: str = Field(..., example="2026-10-01", description="Departure date (YYYY-MM-DD)")
    end_date: str = Field(..., example="2026-10-10", description="Return date (YYYY-MM-DD)")
    budget: float = Field(..., example=2500.0, description="Total travel budget in USD")
    preferences: Optional[str] = Field("", example="Boutique hotel, central location, vegetarian food")

class TripPlanResponse(BaseModel):
    trip_id: Optional[str]
    status: str
    final_itinerary: Dict[str, Any]
    flight_options: List[Dict[str, Any]]
    hotel_options: List[Dict[str, Any]]
    activity_options: List[Dict[str, Any]]
    budget_summary: Dict[str, Any]
    agent_logs: List[Dict[str, Any]]

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "agent-service",
        "duffel_configured": bool(os.getenv("DUFFEL_API_KEY")),
        "flight_provider": os.getenv("FLIGHT_PROVIDER", "duffel"),
        "hotel_provider": os.getenv("HOTEL_PROVIDER", "duffel"),
        "opentripmap_configured": bool(os.getenv("OPENTRIPMAP_API_KEY")),
        "activity_provider": os.getenv("ACTIVITY_PROVIDER", "opentripmap"),
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
        "llm_model": os.getenv("LLM_MODEL", "gemini-2.5-flash"),
        "llm_fallback_model": os.getenv("LLM_FALLBACK_MODEL", "gemini-3.1-flash-lite")
    }

@app.get("/")
def root():
    return {
        "message": "Multi-Agent AI Travel Planner - Agent Service running",
        "docs": "/docs"
    }

@app.post("/plan-trip", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest):
    logger.info(f"Received trip planning request: {request.origin} -> {request.destination} (Budget: ${request.budget})")
    try:
        initial_state: TravelPlanState = {
            "trip_id": request.trip_id,
            "origin": request.origin,
            "destination": request.destination,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "budget": request.budget,
            "preferences": request.preferences or "",
            "flight_options": [],
            "hotel_options": [],
            "activity_options": [],
            "day_plans": [],
            "budget_summary": {},
            "final_itinerary": {},
            "errors": [],
            "agent_logs": []
        }

        # Execute LangGraph graph
        result_state = planner_graph.invoke(initial_state)

        return TripPlanResponse(
            trip_id=request.trip_id,
            status="COMPLETED",
            final_itinerary=result_state.get("final_itinerary", {}),
            flight_options=result_state.get("flight_options", []),
            hotel_options=result_state.get("hotel_options", []),
            activity_options=result_state.get("activity_options", []),
            budget_summary=result_state.get("budget_summary", {}),
            agent_logs=result_state.get("agent_logs", [])
        )
    except Exception as e:
        logger.error(f"Error during trip orchestration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orchestration failure: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
