import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents.orchestrator import create_travel_planner_graph
from agents.state import TravelPlanState
from broadcaster import manager, publish_trip_event
from auth import verify_jwt_token, verify_trip_ownership_db, check_trip_access

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agent-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    manager.set_loop(loop)
    logger.info("Agent-service lifespan initialized with running event loop.")
    yield

app = FastAPI(
    title="Multi-Agent AI Travel Planner - Agent Service",
    description="LangGraph-powered orchestration engine for travel itinerary planning.",
    version="1.0.0",
    lifespan=lifespan
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

@app.websocket("/ws/trip/{trip_id}")
async def websocket_trip_endpoint(
    websocket: WebSocket,
    trip_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time agent execution streaming.
    Streams agent status events (STARTED, SUCCESS, REPLANNING, FAILED, COMPLETED) to connected client.
    Enforces JWT authentication and trip ownership check during the handshake.
    Rejects/closes with code 1008 (Policy Violation) if token is missing/invalid or user does not own the trip.
    """
    str_id = str(trip_id).strip()
    logger.info(f"WebSocket client attempting connection for trip: {str_id}")

    # 1. Extract token from query params (?token=... or ?access_token=...), subprotocol, or headers
    auth_token = token or websocket.query_params.get("token") or websocket.query_params.get("access_token")
    selected_subprotocol = None

    if not auth_token and "sec-websocket-protocol" in websocket.headers:
        sec_protocol = websocket.headers.get("sec-websocket-protocol", "")
        protocols = [p.strip() for p in sec_protocol.split(",") if p.strip()]
        for proto in protocols:
            candidate = proto
            if candidate.lower().startswith("bearer "):
                candidate = candidate[7:].strip()
            elif candidate.lower().startswith("bearer."):
                candidate = candidate[7:].strip()
            if len(candidate) > 20 and candidate.count(".") == 2:
                auth_token = candidate
                selected_subprotocol = proto
                break

    if not auth_token and "authorization" in websocket.headers:
        auth_hdr = websocket.headers.get("authorization", "").strip()
        if auth_hdr.lower().startswith("bearer "):
            auth_token = auth_hdr[7:].strip()
        else:
            auth_token = auth_hdr

    if not auth_token:
        logger.warning(f"WebSocket connection rejected for trip {str_id}: Missing authentication token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized: Missing authentication token")
        return

    # 2. Validate JWT signature and expiration
    payload = verify_jwt_token(auth_token)
    if not payload:
        logger.warning(f"WebSocket connection rejected for trip {str_id}: Invalid or expired token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized: Invalid or expired token")
        return

    user_id = payload.get("sub")
    if not user_id:
        logger.warning(f"WebSocket connection rejected for trip {str_id}: Token missing sub/user_id claim")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized: Missing user identity in token")
        return

    # 3. Confirm trip ownership against database
    # Allows a brief poll window in case client initiated WS immediately prior to / concurrently with POST /api/trips
    is_owner = await check_trip_access(str_id, user_id, max_wait_seconds=3.0)
    if not is_owner:
        logger.warning(f"WebSocket connection rejected for trip {str_id}: User {user_id} does not own this trip")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Forbidden: You do not own this trip")
        return

    # 4. Accept connection and register with connection manager
    logger.info(f"WebSocket connection accepted for user {user_id} on trip: {str_id}")
    await manager.connect(str_id, websocket, subprotocol=selected_subprotocol)
    try:
        while True:
            # Keep socket open; handle optional client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(str_id, websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error on trip {str_id}: {e}")
        manager.disconnect(str_id, websocket)

@app.get("/ws/trip/{trip_id}/events")
def get_trip_events(
    trip_id: str,
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Fallback REST endpoint that returns the in-memory buffered event history
    for a trip id in case the client cannot establish a WebSocket connection.
    Enforces JWT authentication and trip ownership matching.
    """
    str_id = str(trip_id).strip()
    auth_token = token
    if not auth_token and authorization:
        if authorization.lower().startswith("bearer "):
            auth_token = authorization[7:].strip()
        else:
            auth_token = authorization.strip()

    if not auth_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing authentication token")

    payload = verify_jwt_token(auth_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing user identity in token")

    ownership = verify_trip_ownership_db(str_id, user_id)
    if ownership is False:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this trip")
    elif ownership is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    return {
        "trip_id": str_id,
        "events": manager.get_history(str_id)
    }

@app.post("/plan-trip", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest):
    logger.info(f"Received trip planning request: {request.origin} -> {request.destination} (Budget: ${request.budget})")

    if request.trip_id:
        publish_trip_event(
            trip_id=str(request.trip_id),
            agent="Orchestrator Agent",
            status="STARTED",
            message=f"Starting multi-agent trip planning for {request.origin} -> {request.destination} (${request.budget:,.2f} budget)...",
            details={"origin": request.origin, "destination": request.destination, "budget": request.budget}
        )

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

        if request.trip_id:
            flight_cnt = len(result_state.get("flight_options", []))
            hotel_cnt = len(result_state.get("hotel_options", []))
            act_cnt = len(result_state.get("activity_options", []))
            publish_trip_event(
                trip_id=str(request.trip_id),
                agent="Orchestrator Agent",
                status="COMPLETED",
                message=f"Trip planning completed successfully! ({flight_cnt} flights, {hotel_cnt} hotels, {act_cnt} activities curated).",
                details={
                    "status": "COMPLETED",
                    "flight_count": flight_cnt,
                    "hotel_count": hotel_cnt,
                    "activity_count": act_cnt,
                    "budget_summary": result_state.get("budget_summary", {})
                }
            )

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
        if request.trip_id:
            publish_trip_event(
                trip_id=str(request.trip_id),
                agent="Orchestrator Agent",
                status="FAILED",
                message=f"Trip orchestration failed: {str(e)}",
                details={"error": str(e)}
            )
        raise HTTPException(status_code=500, detail=f"Orchestration failure: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
