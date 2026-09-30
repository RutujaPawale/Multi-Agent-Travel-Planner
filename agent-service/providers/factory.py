import os
import logging
from typing import Optional, Tuple

from .base import FlightProvider, HotelProvider, PlacesProvider
from .mock_provider import MockProvider
from .duffel_provider import DuffelProvider
from .opentripmap_provider import OpenTripMapProvider

logger = logging.getLogger("provider_factory")

def resolve_provider_choice(env_var_name: str, default: str = "duffel") -> str:
    """
    Reads provider choice from environment variable.
    """
    val = os.getenv(env_var_name, default).strip().lower()
    return val

def get_flight_provider(
    requested_provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[FlightProvider, bool, Optional[str]]:
    """
    Selects the flight provider based on requested_provider or FLIGHT_PROVIDER env var.
    Defaults to MockProvider if DUFFEL_API_KEY is missing.
    Returns: (provider_instance, is_fallback, fallback_reason)
    """
    target = (requested_provider or resolve_provider_choice("FLIGHT_PROVIDER", "duffel")).strip().lower()
    key = (api_key or os.getenv("DUFFEL_API_KEY", "")).strip()

    if target == "duffel":
        if not key or key == "your_duffel_api_key_here":
            reason = "Missing DUFFEL_API_KEY environment variable"
            logger.info(f"{reason}; defaulting to MockProvider for flights.")
            return MockProvider(), True, reason
        try:
            return DuffelProvider(api_key=key), False, None
        except Exception as e:
            reason = f"DuffelProvider initialization failed: {str(e)}"
            return MockProvider(), True, reason

    reason = "FLIGHT_PROVIDER set to mock" if key else "Missing DUFFEL_API_KEY environment variable"
    return MockProvider(), True, reason

def get_hotel_provider(
    requested_provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[HotelProvider, bool, Optional[str]]:
    """
    Selects the hotel provider based on requested_provider or HOTEL_PROVIDER env var.
    Defaults to MockProvider if DUFFEL_API_KEY is missing.
    Returns: (provider_instance, is_fallback, fallback_reason)
    """
    target = (requested_provider or resolve_provider_choice("HOTEL_PROVIDER", "duffel")).strip().lower()
    key = (api_key or os.getenv("DUFFEL_API_KEY", "")).strip()

    if target == "duffel":
        if not key or key == "your_duffel_api_key_here":
            reason = "Missing DUFFEL_API_KEY environment variable"
            logger.info(f"{reason}; defaulting to MockProvider for hotels.")
            return MockProvider(), True, reason
        try:
            return DuffelProvider(api_key=key), False, None
        except Exception as e:
            reason = f"DuffelProvider initialization failed: {str(e)}"
            return MockProvider(), True, reason

    reason = "HOTEL_PROVIDER set to mock" if key else "Missing DUFFEL_API_KEY environment variable"
    return MockProvider(), True, reason

def get_places_provider(
    requested_provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[PlacesProvider, bool, Optional[str]]:
    """
    Selects the places provider based on requested_provider or ACTIVITY_PROVIDER env var ('opentripmap' | 'mock').
    Defaults to MockProvider if OPENTRIPMAP_API_KEY is missing.
    Returns: (provider_instance, is_fallback, fallback_reason)
    """
    target = (requested_provider or resolve_provider_choice("ACTIVITY_PROVIDER", "opentripmap")).strip().lower()
    key = (api_key or os.getenv("OPENTRIPMAP_API_KEY", "")).strip()

    if target in ("opentripmap", "otm", "open_trip_map", "places"):
        if not key or key == "your_opentripmap_api_key_here":
            reason = "Missing OPENTRIPMAP_API_KEY environment variable"
            logger.info(f"{reason}; defaulting to MockProvider for activities/places.")
            return MockProvider(), True, reason
        try:
            return OpenTripMapProvider(api_key=key), False, None
        except Exception as e:
            reason = f"OpenTripMapProvider initialization failed: {str(e)}"
            return MockProvider(), True, reason

    reason = "ACTIVITY_PROVIDER set to mock" if key else "Missing OPENTRIPMAP_API_KEY environment variable"
    return MockProvider(), True, reason
