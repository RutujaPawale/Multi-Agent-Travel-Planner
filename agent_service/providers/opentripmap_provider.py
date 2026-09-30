import os
import logging
from typing import Any, Dict, List, Optional
import requests

from .base import PlaceItem, PlacesProvider
from .location import resolve_coordinates, resolve_iata, resolve_city_name, IATA_TO_CITY

import re

logger = logging.getLogger("opentripmap_provider")

OPENTRIPMAP_BASE_URL = "https://api.opentripmap.com/0.1/en"

def safe_parse_int(val: Any, default: int = 0) -> int:
    """
    Safely converts an input value to an int.
    Handles int, float, str (including numeric strings with suffixes like '3', '3h', '3.0'),
    None, or non-numeric types gracefully without raising exceptions.
    """
    if val is None:
        return default
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int, float)):
        try:
            return int(val)
        except (ValueError, OverflowError):
            return default
    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return default
        try:
            return int(float(cleaned))
        except ValueError:
            # Handle cases where non-digit characters are appended, e.g. "3h"
            digits = []
            for ch in cleaned:
                if ch.isdigit():
                    digits.append(ch)
                elif digits:
                    break
            if digits:
                try:
                    return int("".join(digits))
                except ValueError:
                    return default
            return default
    return default

def safe_parse_float(val: Any, default: float = 0.0) -> float:
    """
    Safely converts an input value to a float.
    Handles float, int, str, None, or non-numeric types gracefully.
    """
    if val is None:
        return default
    if isinstance(val, bool):
        return float(val)
    if isinstance(val, (int, float)):
        try:
            return float(val)
        except (ValueError, OverflowError):
            return default
    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            match = re.search(r"[-+]?\d*\.?\d+", cleaned)
            if match:
                try:
                    return float(match.group(0))
                except ValueError:
                    return default
            return default
    return default

def map_kinds_to_category(kinds_str: str) -> str:
    """Maps OpenTripMap kinds string to user-friendly category name."""
    kinds = [k.strip().lower() for k in (kinds_str or "").split(",") if k.strip()]
    if any(k in kinds for k in ["museums", "art_galleries", "cultural"]):
        return "Art & Culture"
    if any(k in kinds for k in ["foods", "restaurants", "cafes", "bars", "pubs"]):
        return "Food & Culinary"
    if any(k in kinds for k in ["gardens_and_parks", "natural"]):
        return "Park & Nature"
    if any(k in kinds for k in ["historic", "monuments_and_memorials", "historic_architecture", "castles"]):
        return "Historic Landmark"
    if any(k in kinds for k in ["view_points", "architecture", "skyscrapers"]):
        return "Landmark & Views"
    return "Sightseeing & Tour"

def estimate_cost_for_category(category: str) -> float:
    """Estimates realistic per-person activity cost in USD based on category."""
    cost_map = {
        "Art & Culture": 24.0,
        "Food & Culinary": 45.0,
        "Park & Nature": 10.0,
        "Historic Landmark": 18.0,
        "Landmark & Views": 32.0,
        "Sightseeing & Tour": 25.0
    }
    return cost_map.get(category, 25.0)

def format_address(address_dict: Optional[Dict[str, Any]], fallback_city: str) -> str:
    """Formats OpenTripMap address dictionary into a clean display string."""
    if not address_dict or not isinstance(address_dict, dict):
        return f"{fallback_city}, City Center"

    parts = []
    house_num = address_dict.get("house_number")
    road = address_dict.get("road") or address_dict.get("pedestrian")
    if road:
        parts.append(f"{house_num} {road}".strip() if house_num else road)

    district = (
        address_dict.get("suburb")
        or address_dict.get("neighbourhood")
        or address_dict.get("city_district")
        or address_dict.get("quarter")
    )
    if district:
        parts.append(district)

    city = (
        address_dict.get("city")
        or address_dict.get("town")
        or address_dict.get("village")
        or fallback_city
    )
    if city and city not in parts:
        parts.append(city)

    return ", ".join(parts) if parts else f"{fallback_city}, City Center"

class OpenTripMapProvider(PlacesProvider):
    """
    Live Places provider integrating with the OpenTripMap API (https://opentripmap.io):
    1. Geocodes destination city/airport to coordinates via /places/geoname or location registry.
    2. Searches points of interest via /places/radius filtered by kinds matching user preferences.
    3. Fetches rich metadata (address, description, rating) for top candidates via /places/xid/{xid}.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("OPENTRIPMAP_API_KEY", "")).strip()
        if not self.api_key or self.api_key == "your_opentripmap_api_key_here":
            raise ValueError("Missing OPENTRIPMAP_API_KEY environment variable")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def geocode_destination(self, destination: str) -> Dict[str, float]:
        """
        Resolves destination to latitude and longitude.
        1. Checks if the destination is a 3-letter IATA airport/metro code (e.g. CDG, JFK, LHR, NRT).
           If so, maps it to its proper city name (e.g. CDG -> Paris, JFK -> New York) BEFORE calling
           OpenTripMap /places/geoname, preventing erroneous matches (e.g. CDG -> Córdoba, Argentina).
        2. Calls OpenTripMap /places/geoname with the resolved city name.
        3. Falls back to the location registry (resolve_coordinates) if the API fails or returns no coordinates.
        """
        cleaned = destination.strip()
        city_name = resolve_city_name(cleaned)
        is_iata = cleaned.upper() in IATA_TO_CITY

        search_query = city_name if is_iata else cleaned

        # Query OpenTripMap geoname endpoint using proper city name
        try:
            url = f"{OPENTRIPMAP_BASE_URL}/places/geoname"
            resp = self.session.get(
                url,
                params={"name": search_query, "apikey": self.api_key},
                timeout=8
            )
            if resp.status_code == 200:
                data = resp.json()
                if "lat" in data and "lon" in data:
                    lat = safe_parse_float(data["lat"], default=0.0)
                    lon = safe_parse_float(data["lon"], default=0.0)
                    if lat != 0.0 or lon != 0.0:
                        logger.info(
                            f"OpenTripMap geoname resolved '{destination}' (via '{search_query}') "
                            f"to ({lat}, {lon}) in {data.get('country', '')}"
                        )
                        return {"latitude": lat, "longitude": lon}
        except Exception as e:
            logger.warning(f"OpenTripMap geoname request failed for '{destination}' ('{search_query}'): {e}")

        # Fallback to local coordinate registry (handles airport codes like CDG, JFK, LHR, NRT, etc.)
        coords = resolve_coordinates(cleaned)
        logger.info(f"Using location registry coordinates for '{destination}': {coords}")
        return coords

    def build_kinds_filter(self, preferences: str) -> str:
        """
        Maps traveler preferences to OpenTripMap kind tags.
        """
        pref_lower = (preferences or "").lower()
        selected_kinds: List[str] = []

        if any(w in pref_lower for w in ["art", "museum", "gallery", "exhibit"]):
            selected_kinds.extend(["museums", "art_galleries", "cultural"])

        if any(w in pref_lower for w in ["food", "culinary", "restaurant", "dining", "tour", "bistro", "wine", "tasting", "cafe", "market"]):
            selected_kinds.extend(["foods", "restaurants", "cafes"])

        if any(w in pref_lower for w in ["history", "historic", "architecture", "monument", "cathedral", "church", "heritage", "palace", "castle"]):
            selected_kinds.extend(["historic", "architecture", "monuments_and_memorials"])

        if any(w in pref_lower for w in ["park", "nature", "outdoor", "garden", "walk", "green", "botanic"]):
            selected_kinds.extend(["gardens_and_parks", "natural"])

        if any(w in pref_lower for w in ["view", "skyline", "panorama", "deck", "observation", "tower"]):
            selected_kinds.extend(["view_points", "architecture"])

        if not selected_kinds:
            # Broad default covering cultural, historic, food, and tourist attractions
            selected_kinds = ["interesting_places", "cultural", "museums", "historic", "foods"]

        # Deduplicate while preserving order
        return ",".join(dict.fromkeys(selected_kinds))

    def fetch_places(
        self,
        destination: str,
        preferences: str = "",
        limit: int = 15
    ) -> List[PlaceItem]:
        """
        Queries OpenTripMap /places/radius endpoint, selects top candidate places,
        and retrieves detailed metadata via /places/xid/{xid}.
        """
        coords = self.geocode_destination(destination)
        lat = coords["latitude"]
        lon = coords["longitude"]
        kinds = self.build_kinds_filter(preferences)

        radius_url = f"{OPENTRIPMAP_BASE_URL}/places/radius"
        fetch_limit = min(50, max(25, limit * 2))

        # Attempt query with rate=2 (notable attractions) first
        candidate_items = self._query_radius(radius_url, lat, lon, kinds, rate=2, limit=fetch_limit)

        # If too few candidates returned, broaden search with rate=1 or no rate
        if len(candidate_items) < 6:
            logger.info("Fewer than 6 candidates found with rate=2; broadening OpenTripMap search with rate=1...")
            candidate_items = self._query_radius(radius_url, lat, lon, kinds, rate=1, limit=fetch_limit)

        if not candidate_items:
            # Try without kinds restriction if kinds was overly narrow
            logger.info("Broadening OpenTripMap search to general interesting_places...")
            candidate_items = self._query_radius(radius_url, lat, lon, "interesting_places,cultural,foods", rate=1, limit=fetch_limit)

        # Sort candidate items by rate (descending) and dist (ascending) to prioritize top-rated places
        def candidate_sort_key(item: Dict[str, Any]):
            item_rate = safe_parse_int(item.get("rate"), default=0)
            item_dist = safe_parse_float(item.get("dist"), default=999999.0)
            return (-item_rate, item_dist)

        sorted_candidates = sorted(candidate_items, key=candidate_sort_key)

        # Filter out unnamed entries and deduplicate by name
        filtered_candidates: List[Dict[str, Any]] = []
        seen_names = set()

        for item in sorted_candidates:
            name = (item.get("name") or "").strip()
            if not name:
                continue
            name_key = name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)
            filtered_candidates.append(item)
            if len(filtered_candidates) >= limit:
                break

        if not filtered_candidates:
            logger.warning(f"OpenTripMap returned 0 named places for destination: {destination}")
            return []

        # Step 2: Fetch details for top candidates using /places/xid/{xid}
        detailed_places: List[PlaceItem] = []
        dest_title = resolve_city_name(destination)

        for cand in filtered_candidates:
            xid = cand.get("xid")
            cand_name = cand.get("name", "Attraction")
            cand_point = cand.get("point") if isinstance(cand.get("point"), dict) else {}
            cand_lat = safe_parse_float(cand_point.get("lat"), default=lat)
            cand_lon = safe_parse_float(cand_point.get("lon"), default=lon)
            cand_rate = safe_parse_int(cand.get("rate"), default=2)
            cand_kinds = cand.get("kinds", kinds)

            detail_data: Dict[str, Any] = {}
            if xid:
                try:
                    xid_url = f"{OPENTRIPMAP_BASE_URL}/places/xid/{xid}"
                    xid_resp = self.session.get(
                        xid_url,
                        params={"apikey": self.api_key},
                        timeout=6
                    )
                    if xid_resp.status_code == 200:
                        detail_data = xid_resp.json()
                    else:
                        logger.debug(f"OpenTripMap xid {xid} returned status {xid_resp.status_code}")
                except Exception as e:
                    logger.debug(f"OpenTripMap xid {xid} fetch failed: {e}")

            # Merge detail attributes
            name = (detail_data.get("name") or cand_name).strip()
            item_kinds = detail_data.get("kinds") or cand_kinds
            category = map_kinds_to_category(item_kinds)
            estimated_cost = estimate_cost_for_category(category)

            # Rating mapping (rate is 1..3 in OpenTripMap, but detail or cand can return str, int, or null)
            detail_rate_raw = detail_data.get("rate")
            rate_num = safe_parse_int(detail_rate_raw if detail_rate_raw is not None else cand_rate, default=2)
            if rate_num >= 3:
                rating = 4.9
            elif rate_num == 2:
                rating = 4.6
            elif rate_num == 1:
                rating = 4.3
            else:
                rating = 4.5

            # Address formatting
            address_str = format_address(detail_data.get("address"), dest_title)

            # Description extraction
            description = None
            extracts = detail_data.get("wikipedia_extracts")
            if isinstance(extracts, dict) and extracts.get("text"):
                text = extracts.get("text", "").strip()
                description = (text[:180] + "...") if len(text) > 180 else text
            elif detail_data.get("info") and isinstance(detail_data.get("info"), dict):
                descr = detail_data["info"].get("descr")
                if descr:
                    description = (descr[:180] + "...") if len(descr) > 180 else descr

            if not description:
                description = f"Popular {category.lower()} attraction in {dest_title}."

            point_dict = detail_data.get("point") if isinstance(detail_data.get("point"), dict) else cand_point
            item_lat = safe_parse_float(point_dict.get("lat"), default=cand_lat)
            item_lon = safe_parse_float(point_dict.get("lon"), default=cand_lon)

            place_item = PlaceItem(
                id=xid or f"OTM-{len(detailed_places) + 1}",
                name=name,
                category=category,
                address=address_str,
                rating=rating,
                coordinates={"latitude": round(item_lat, 5), "longitude": round(item_lon, 5)},
                types=[k.strip() for k in item_kinds.split(",") if k.strip()][:5],
                estimated_cost=estimated_cost,
                description=description,
                source="OpenTripMap API",
                is_mock=False
            )
            detailed_places.append(place_item)

        logger.info(f"OpenTripMap successfully fetched and enriched {len(detailed_places)} places for {destination}")
        return detailed_places

    def _query_radius(
        self,
        url: str,
        lat: float,
        lon: float,
        kinds: str,
        rate: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Helper to invoke OpenTripMap radius endpoint."""
        params: Dict[str, Any] = {
            "radius": 15000,
            "lon": lon,
            "lat": lat,
            "kinds": kinds,
            "format": "json",
            "limit": limit,
            "apikey": self.api_key
        }
        if rate is not None:
            params["rate"] = rate

        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                logger.warning(f"OpenTripMap radius endpoint returned unexpected JSON: {data}")
                return []
            if resp.status_code in (401, 403):
                raise ValueError(f"HTTP status {resp.status_code}: Invalid or unauthorized OPENTRIPMAP_API_KEY")
            logger.warning(f"OpenTripMap radius search returned status {resp.status_code}: {resp.text[:150]}")
            return []
        except requests.RequestException as e:
            logger.warning(f"OpenTripMap radius request error: {e}")
            raise
