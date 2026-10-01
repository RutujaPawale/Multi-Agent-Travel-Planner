import os
import json
import logging
from typing import Any, Optional
import psycopg2
from psycopg2.extras import Json

try:
    from broadcaster import publish_trip_event
except (ImportError, ModuleNotFoundError):
    try:
        from agent_service.broadcaster import publish_trip_event
    except (ImportError, ModuleNotFoundError):
        publish_trip_event = None

logger = logging.getLogger("agent_logger")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/travel_planner")

def get_db_connection():
    """Returns a psycopg2 database connection or None if unavailable."""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=2)
        return conn
    except Exception as e:
        logger.warning(f"Could not connect to database at {DATABASE_URL}: {e}")
        return None

def extract_agent_message(agent_name: str, output_data: Any, status: str, error_message: Optional[str]) -> str:
    """Extracts human-readable reason/message already logged to agent_runs for WebSocket feed."""
    msg = ""
    if isinstance(output_data, dict):
        if status == "REPLANNING" and output_data.get("reason"):
            msg = output_data["reason"]
        elif output_data.get("summary"):
            msg = output_data["summary"]
        elif output_data.get("filter_message"):
            msg = output_data["filter_message"]
        elif output_data.get("reason"):
            msg = output_data["reason"]
        elif output_data.get("message"):
            msg = output_data["message"]

    if not msg and error_message:
        msg = error_message

    if not msg:
        if agent_name == "Flight Agent":
            count = output_data.get("flight_count", 0) if isinstance(output_data, dict) else 0
            msg = f"Found {count} flight options."
        elif agent_name == "Hotel Agent":
            count = output_data.get("hotel_count", 0) if isinstance(output_data, dict) else 0
            msg = f"Selected {count} hotel options."
        elif agent_name == "Activity Agent":
            count = output_data.get("activity_count", 0) if isinstance(output_data, dict) else 0
            msg = f"Generated {count} scheduled activities."
        elif agent_name == "Budget Agent":
            msg = "Budget analysis completed."
        else:
            msg = f"{agent_name} completed step with status {status}."

    return msg

def log_agent_run(
    trip_id: Optional[str],
    agent_name: str,
    input_data: Any,
    output_data: Any,
    status: str,
    error_message: Optional[str] = None
) -> Optional[str]:
    """
    Logs an agent invocation step to the agent_runs table in PostgreSQL.
    Input/output data are converted to JSON.
    Also broadcasts the status event via WebSocket.
    """
    logger.info(f"[{agent_name}] Status: {status} | Trip: {trip_id}")

    # Broadcast event via WebSocket in real-time
    if publish_trip_event and trip_id:
        try:
            ws_msg = extract_agent_message(agent_name, output_data, status, error_message)
            publish_trip_event(
                trip_id=str(trip_id),
                agent=agent_name,
                status=status,
                message=ws_msg,
                details=output_data if isinstance(output_data, dict) else {"data": str(output_data)}
            )
        except Exception as ws_err:
            logger.warning(f"Error publishing WebSocket event from log_agent_run: {ws_err}")
    
    conn = get_db_connection()
    if not conn:
        logger.info(f"[{agent_name}] Database logging skipped (no DB connection). Input: {input_data} | Output: {output_data}")
        return None

    try:
        with conn:
            with conn.cursor() as cur:
                # trip_id is a UUID or NULL
                clean_trip_id = trip_id if trip_id and len(str(trip_id)) > 10 else None
                
                cur.execute(
                    """
                    INSERT INTO agent_runs (trip_id, agent_name, input_data, output_data, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        clean_trip_id,
                        agent_name,
                        Json(input_data if isinstance(input_data, (dict, list)) else {"value": str(input_data)}),
                        Json(output_data if isinstance(output_data, (dict, list)) else {"value": str(output_data)}),
                        status,
                        error_message
                    )
                )
                run_id = cur.fetchone()[0]
                logger.info(f"Logged agent run {run_id} for {agent_name}")
                return str(run_id)
    except Exception as e:
        logger.error(f"Failed to log agent run to database: {e}", exc_info=True)
        return None
    finally:
        conn.close()

def update_agent_run(
    run_id: str,
    output_data: Any,
    status: str,
    error_message: Optional[str] = None
) -> bool:
    """
    Updates an existing agent_runs record (e.g. transitioning Orchestrator from IN_PROGRESS to SUCCESS).
    """
    if not run_id:
        return False

    logger.info(f"[Update Agent Run] ID: {run_id} | Status: {status}")
    conn = get_db_connection()
    if not conn:
        logger.info(f"Database update skipped for run_id {run_id} (no DB connection). Status: {status}")
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET output_data = %s, status = %s, error_message = %s
                    WHERE id = %s;
                    """,
                    (
                        Json(output_data if isinstance(output_data, (dict, list)) else {"value": str(output_data)}),
                        status,
                        error_message,
                        run_id
                    )
                )
                logger.info(f"Updated agent run {run_id} to status {status}")
                return True
    except Exception as e:
        logger.error(f"Failed to update agent run {run_id} in database: {e}", exc_info=True)
        return False
    finally:
        conn.close()

