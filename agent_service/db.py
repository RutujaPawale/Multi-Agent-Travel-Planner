import os
import json
import logging
from typing import Any, Optional
import psycopg2
from psycopg2.extras import Json

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
    """
    logger.info(f"[{agent_name}] Status: {status} | Trip: {trip_id}")
    
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

