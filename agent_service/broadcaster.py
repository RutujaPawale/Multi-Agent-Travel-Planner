import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import WebSocket

logger = logging.getLogger("broadcaster")

class ConnectionManager:
    """
    Manages real-time WebSocket connections and event history buffering for trip planning runs.
    Supports thread-safe event publishing from background worker threads.
    """

    def __init__(self):
        # trip_id -> list of active WebSocket clients
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # trip_id -> list of buffered event dicts
        self.history: Dict[str, List[Dict[str, Any]]] = {}
        # Reference to the main asyncio event loop
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        logger.info(f"WebSocket ConnectionManager event loop set: {loop}")

    async def connect(self, trip_id: str, websocket: WebSocket, subprotocol: Optional[str] = None):
        await websocket.accept(subprotocol=subprotocol)
        str_id = str(trip_id)
        if str_id not in self.active_connections:
            self.active_connections[str_id] = []
        self.active_connections[str_id].append(websocket)
        logger.info(f"WebSocket client connected for trip {str_id}. Active count: {len(self.active_connections[str_id])}")

        # Replay event history for this trip so client immediately catches up
        buffered = self.history.get(str_id, [])
        for event in buffered:
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.warning(f"Failed to replay buffered event to client: {e}")
                break

    def disconnect(self, trip_id: str, websocket: WebSocket):
        str_id = str(trip_id)
        if str_id in self.active_connections:
            if websocket in self.active_connections[str_id]:
                self.active_connections[str_id].remove(websocket)
            if not self.active_connections[str_id]:
                del self.active_connections[str_id]
        logger.info(f"WebSocket client disconnected for trip {str_id}")

    async def _send_event_async(self, trip_id: str, event: Dict[str, Any]):
        """Internal coroutine to deliver an event to all connected sockets for a trip."""
        connections = self.active_connections.get(trip_id, [])
        dead_sockets = []
        for ws in connections:
            try:
                await ws.send_json(event)
            except Exception as e:
                logger.warning(f"Error broadcasting to socket on trip {trip_id}: {e}")
                dead_sockets.append(ws)

        for dead in dead_sockets:
            self.disconnect(trip_id, dead)

    def publish_event(
        self,
        trip_id: Optional[str],
        agent: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publishes a real-time status event to connected WebSocket clients and appends to history.
        Thread-safe: schedules async coroutine on main event loop if called from a worker thread.
        """
        if not trip_id:
            return {}

        str_id = str(trip_id).strip()
        timestamp = datetime.utcnow().isoformat() + "Z"
        event = {
            "trip_id": str_id,
            "agent": agent,
            "status": status,  # "STARTED" | "SUCCESS" | "REPLANNING" | "FAILED" | "COMPLETED"
            "message": message,
            "stage": stage or agent.lower().replace(" ", "_"),
            "details": details or {},
            "timestamp": timestamp
        }

        # Buffer in history (cap history at 50 events per trip to prevent memory bloat)
        if str_id not in self.history:
            self.history[str_id] = []
        self.history[str_id].append(event)
        if len(self.history[str_id]) > 50:
            self.history[str_id] = self.history[str_id][-50:]

        # Dispatch async broadcast safely
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._send_event_async(str_id, event), self.loop)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(self._send_event_async(str_id, event), loop)
            except Exception as e:
                logger.warning(f"Could not find running event loop for event broadcast: {e}")

        return event

    def get_history(self, trip_id: str) -> List[Dict[str, Any]]:
        """Returns buffered events for a trip id (used by REST polling fallback)."""
        return list(self.history.get(str(trip_id), []))

# Singleton instance
manager = ConnectionManager()

def publish_trip_event(
    trip_id: Optional[str],
    agent: str,
    status: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    stage: Optional[str] = None
) -> Dict[str, Any]:
    """Helper shortcut function to publish a trip status event."""
    return manager.publish_event(
        trip_id=trip_id,
        agent=agent,
        status=status,
        message=message,
        details=details,
        stage=stage
    )
