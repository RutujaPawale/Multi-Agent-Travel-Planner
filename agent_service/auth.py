import os
import asyncio
import logging
from typing import Optional, Dict, Any
import jwt
from db import get_db_connection

logger = logging.getLogger("agent-auth")

DEFAULT_JWT_SECRET = "MultiAgentTravelPlannerSecureSecretKeyForSigningJwtTokens1234567890"

def get_jwt_secret() -> str:
    return os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET)

def verify_jwt_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Validates a JWT token and returns its decoded payload claims if valid.
    Returns None if missing, expired, or invalid.
    """
    if not token:
        return None

    clean_token = token.strip()
    if clean_token.lower().startswith("bearer "):
        clean_token = clean_token[7:].strip()

    secret = get_jwt_secret()

    try:
        payload = jwt.decode(
            clean_token,
            secret,
            algorithms=["HS256", "HS384", "HS512"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT verification failed: Invalid token ({e})")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating JWT token: {e}", exc_info=True)
        return None

def verify_trip_ownership_db(trip_id: str, user_id: str) -> Optional[bool]:
    """
    Checks database for trip ownership:
    - Returns True if trip exists and user_id matches.
    - Returns False if trip exists and user_id does NOT match (forbidden).
    - Returns None if trip record does not exist in the database yet.
    """
    conn = get_db_connection()
    if not conn:
        logger.warning("Database connection unavailable for trip ownership check.")
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM trips WHERE id = %s;", (trip_id,))
                row = cur.fetchone()
                if not row:
                    return None
                
                db_user_id = str(row[0]).strip().lower()
                req_user_id = str(user_id).strip().lower()
                return db_user_id == req_user_id
    except Exception as e:
        logger.error(f"Database error checking trip ownership for trip {trip_id}: {e}", exc_info=True)
        return False
    finally:
        conn.close()

async def check_trip_access(trip_id: str, user_id: str, max_wait_seconds: float = 3.0) -> bool:
    """
    Verifies that the given user_id owns the trip.
    If the trip record has not yet been committed to PostgreSQL (e.g. WebSocket connection
    opened concurrently with trip creation request), retries briefly up to max_wait_seconds.
    """
    elapsed = 0.0
    poll_interval = 0.2

    while elapsed <= max_wait_seconds:
        ownership = verify_trip_ownership_db(trip_id, user_id)
        if ownership is True:
            logger.info(f"Trip ownership verified: User {user_id} owns trip {trip_id}")
            return True
        elif ownership is False:
            logger.warning(f"Trip ownership rejected: User {user_id} does NOT own trip {trip_id}")
            return False
        
        # If None, trip is not in DB yet; wait briefly for api-service saveAndFlush
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    logger.warning(f"Trip ownership timeout: Trip {trip_id} not found in database within {max_wait_seconds}s")
    return False
