import os
import logging
from typing import Any, Dict, List, Optional
import httpx

from .base import PlaceItem, PlacesProvider
from .location import resolve_coordinates

logger = logging.getLogger("google_places_provider")

GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

CATEGORY_TYPE_MAP = {
    "museum": "Museum & Art",
    "art_gallery": "Museum & Art",
    "tourist_attraction": "Sightseeing & Culture",
    "historical_landmark": "Sightseeing & Culture",
    "church": "Sightseeing & Culture",
    "place_of_worship": "Sightseeing & Culture",
    "restaurant": "Food & Culinary",
    "food": "Food & Culinary",
    "cafe": "Food & Culinary",
    "bakery": "Food & Culinary",
    "bar": "Food & Culinary",
    "park": "Park & Nature",
    "natural_feature": "Park & Nature",
    "zoo": "Entertainment & Animals",
    "aquarium": "Entertainment & Animals",
    "amusement_park": "Entertainment & Adventure"
}

ESTIMATED_COST_MAP = {
    "Museum & Art": 25.0,
    "Sightseeing & Culture": 20.0,
    "Food & Culinary": 50.0,
    "Park & Nature": 12.0,
    "Entertainment & Animals": 35.0,
    "Entertainment & Adventure": 45.0
}

class GooglePlacesProvider(PlacesProvider):
    """
    Live Places provider integrating with Google Places API (New) Text Search:
    POST https://places.googleapis.com/v1/places:searchText
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("PLACES_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY", "")).strip()
        if not self.api_key or self.api_key == "your_places_api_key_here":
            raise ValueError("Missing PLACES_API_KEY environment variable")

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.types,places.location,places.editorialSummary,places.priceLevel"
        }

    def fetch_places(
        self,
        destination: str,
        preferences: str = "",
        limit: int = 15
    ) -> List[PlaceItem]:
        """
        Queries Google Places API Text Search for top attractions and points of interest
        matching the traveler's destination and preferences.
        """
        pref_clean = f", focusing on {preferences}" if preferences else ""
        query = f"top attractions, sights, restaurants, and points of interest in {destination}{pref_clean}"

        payload = {
            "textQuery": query,
            "maxResultCount": min(20, max(limit, 10))
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                GOOGLE_PLACES_TEXT_SEARCH_URL,
                headers=self._headers(),
                json=payload
            )

            if resp.status_code != 200:
                err_text = resp.text
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message") or err_text
                except Exception:
                    err_msg = err_text
                logger.warning(f"Google Places API request failed with status {resp.status_code}: {err_msg}")
                raise RuntimeError(f"HTTP status {resp.status_code}: {err_msg}")

            data = resp.json()
            raw_places = data.get("places", [])
            if not raw_places:
                logger.info("Google Places API returned zero places.")
                return []

            parsed_items: List[PlaceItem] = []
            for idx, p in enumerate(raw_places):
                try:
                    pid = p.get("id") or f"PLC-GGL-{idx+1}"
                    name = p.get("displayName", {}).get("text") or f"Place in {destination}"
                    address = p.get("formattedAddress") or destination
                    rating = float(p.get("rating", 4.5))

                    types = p.get("types", [])
                    category = "Sightseeing & Culture"
                    for t in types:
                        if t in CATEGORY_TYPE_MAP:
                            category = CATEGORY_TYPE_MAP[t]
                            break

                    loc = p.get("location", {})
                    coordinates = None
                    if loc.get("latitude") and loc.get("longitude"):
                        coordinates = {
                            "latitude": float(loc["latitude"]),
                            "longitude": float(loc["longitude"])
                        }

                    # Determine reasonable estimated cost based on category and price level
                    base_cost = ESTIMATED_COST_MAP.get(category, 25.0)
                    price_level = p.get("priceLevel")
                    if price_level == "PRICE_LEVEL_EXPENSIVE":
                        base_cost *= 1.8
                    elif price_level == "PRICE_LEVEL_VERY_EXPENSIVE":
                        base_cost *= 2.5
                    elif price_level == "PRICE_LEVEL_INEXPENSIVE":
                        base_cost *= 0.6
                    elif price_level == "PRICE_LEVEL_FREE":
                        base_cost = 0.0

                    editorial = p.get("editorialSummary", {}).get("text")
                    desc = editorial or f"A top-rated {category.lower()} experience in {destination}."

                    parsed_items.append(PlaceItem(
                        id=pid,
                        name=name,
                        category=category,
                        address=address,
                        rating=rating,
                        coordinates=coordinates,
                        types=types,
                        estimated_cost=round(base_cost, 2),
                        description=desc,
                        source="Google Places API",
                        is_mock=False
                    ))
                except Exception as e:
                    logger.warning(f"Error parsing Google Place item: {e}")

            return parsed_items[:limit]
