import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from .base import FlightOption, HotelOption, FlightProvider, HotelProvider
from .location import resolve_iata, resolve_coordinates

logger = logging.getLogger("duffel_provider")

class DuffelProvider(FlightProvider, HotelProvider):
    """
    Live flight and hotel provider integrating with Duffel API (v2).
    - Flights: POST https://api.duffel.com/air/offer_requests?return_offers=true
    - Hotels: POST https://api.duffel.com/stays/search
    Authentication via DUFFEL_API_KEY (Bearer token).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("DUFFEL_API_KEY", "")).strip()
        if not self.api_key or self.api_key == "your_duffel_api_key_here":
            raise ValueError("Missing DUFFEL_API_KEY environment variable")
        self.base_url = "https://api.duffel.com"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Duffel-Version": "v2",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _extract_error_message(self, resp: httpx.Response) -> str:
        """Parses Duffel error payloads into concise human-readable descriptions."""
        try:
            err_json = resp.json()
            errors = err_json.get("errors", [])
            if errors:
                msgs = [e.get("message") or e.get("title") or str(e) for e in errors]
                return "; ".join(msgs)
        except Exception:
            pass
        return resp.text or f"HTTP {resp.status_code}"

    def search_flights(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float
    ) -> List[FlightOption]:
        """
        Creates an Offer Request with Duffel Air API and returns the top 3
        flights ranked by price ascending.
        """
        origin_iata = resolve_iata(origin)
        dest_iata = resolve_iata(destination)

        slices = [
            {
                "origin": origin_iata,
                "destination": dest_iata,
                "departure_date": start_date
            }
        ]
        if end_date and end_date > start_date:
            slices.append({
                "origin": dest_iata,
                "destination": origin_iata,
                "departure_date": end_date
            })

        payload = {
            "data": {
                "slices": slices,
                "passengers": [{"type": "adult"}],
                "cabin_class": "economy"
            }
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{self.base_url}/air/offer_requests?return_offers=true",
                headers=self._headers(),
                json=payload
            )

            if resp.status_code not in (200, 201):
                err_text = self._extract_error_message(resp)
                logger.warning(f"Duffel flight search failed with status {resp.status_code}: {err_text}")
                raise RuntimeError(f"HTTP status {resp.status_code}: {err_text}")

            resp_data = resp.json().get("data", {})
            offers = resp_data.get("offers", [])
            if not offers:
                logger.info("Duffel returned zero flight offers for given route and dates.")
                return []

            # Sort by total_amount ascending
            def parse_offer_price(offer):
                try:
                    return float(offer.get("total_amount", 0.0))
                except (ValueError, TypeError):
                    return float("inf")

            sorted_offers = sorted(offers, key=parse_offer_price)
            top_3 = sorted_offers[:3]

            formatted_flights: List[FlightOption] = []
            for i, offer in enumerate(top_3):
                try:
                    offer_slices = offer.get("slices", [])
                    outbound = offer_slices[0] if offer_slices else {}
                    segments = outbound.get("segments", [])
                    first_seg = segments[0] if segments else {}
                    last_seg = segments[-1] if segments else {}

                    carrier_obj = first_seg.get("marketing_carrier") or first_seg.get("operating_carrier") or {}
                    carrier_name = carrier_obj.get("name") or carrier_obj.get("iata_code") or "Commercial Airline"
                    carrier_code = carrier_obj.get("iata_code", "")
                    flight_num = first_seg.get("marketing_carrier_flight_number") or first_seg.get("operating_carrier_flight_number") or ""
                    flight_identifier = f"{carrier_code} {flight_num}".strip() if carrier_code or flight_num else f"Flight #{i+1}"

                    price = float(offer.get("total_amount", 0.0))
                    currency = offer.get("total_currency", "USD")
                    departure_time = first_seg.get("departing_at") or f"{start_date}T09:00:00"
                    arrival_time = last_seg.get("arriving_at") or f"{start_date}T17:00:00"
                    duration_str = outbound.get("duration", "N/A").replace("PT", "").lower()
                    stops = max(0, len(segments) - 1)

                    formatted_flights.append(FlightOption(
                        rank=i + 1,
                        id=offer.get("id", f"off_{i+1}"),
                        airline=carrier_name,
                        flight_number=flight_identifier,
                        origin=origin_iata,
                        destination=dest_iata,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        duration=duration_str,
                        stops=stops,
                        price=price,
                        currency=currency,
                        source="Duffel Live API",
                        is_mock=False,
                        notes=f"{'Non-stop' if stops == 0 else f'{stops} stop(s)'} flight via {carrier_name}"
                    ))
                except Exception as parse_err:
                    logger.warning(f"Error parsing Duffel flight offer: {parse_err}")

            return formatted_flights

    def search_hotels(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        per_night_cap: float,
        nights: int
    ) -> List[HotelOption]:
        """
        Searches hotels with Duffel Stays Search API, filters by per_night_cap,
        and returns the top 3 ranked by rating (descending) and price (ascending).
        """
        coords = resolve_coordinates(destination)

        payload = {
            "data": {
                "check_in_date": start_date,
                "check_out_date": end_date,
                "guests": [{"type": "adult"}],
                "rooms": 1,
                "location": {
                    "radius": 20,
                    "geographic_coordinates": coords
                }
            }
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{self.base_url}/stays/search",
                headers=self._headers(),
                json=payload
            )

            if resp.status_code not in (200, 201):
                err_text = self._extract_error_message(resp)
                logger.warning(f"Duffel Stays search failed with status {resp.status_code}: {err_text}")
                raise RuntimeError(f"HTTP status {resp.status_code}: {err_text}")

            resp_data = resp.json().get("data", {})
            results = resp_data.get("results", [])
            if not results:
                logger.info("Duffel Stays search returned zero accommodations.")
                return []

            parsed_hotels: List[HotelOption] = []
            for r in results:
                try:
                    accommodation = r.get("accommodation", {})
                    hid = accommodation.get("id") or r.get("id", "HOTEL")
                    name = accommodation.get("name", f"Hotel {hid}").title()

                    raw_rating = accommodation.get("rating")
                    try:
                        rating = float(raw_rating) if raw_rating is not None else 4.2
                    except (ValueError, TypeError):
                        rating = 4.2

                    total_price = float(r.get("cheapest_rate_total_amount", 0.0))
                    currency = r.get("cheapest_rate_currency", "USD")
                    price_per_night = round(total_price / max(1, nights), 2)
                    link = f"https://duffel.com/stays/{hid}"

                    raw_amenities = accommodation.get("amenities", [])
                    amenities = []
                    for am in raw_amenities[:4]:
                        if isinstance(am, dict):
                            amenities.append(am.get("description") or am.get("type", "Amenity"))
                        elif isinstance(am, str):
                            amenities.append(am)
                    if not amenities:
                        amenities = ["Wi-Fi", "Air Conditioning", "En-suite Bathroom"]

                    parsed_hotels.append(HotelOption(
                        id=hid,
                        name=name,
                        rating=rating,
                        price_per_night=price_per_night,
                        total_price=total_price,
                        currency=currency,
                        link=link,
                        neighborhood=destination.title(),
                        amenities=amenities,
                        source="Duffel Live API",
                        is_mock=False
                    ))
                except Exception as parse_err:
                    logger.warning(f"Error parsing Duffel hotel result: {parse_err}")

            if not parsed_hotels:
                return []

            # Filter by per-night budget cap
            within_budget = [h for h in parsed_hotels if h.price_per_night <= per_night_cap]
            candidates = within_budget if within_budget else parsed_hotels

            # Rank by rating (descending), then price (ascending)
            ranked = sorted(
                candidates,
                key=lambda h: (-h.rating, h.price_per_night)
            )

            top_3 = ranked[:3]
            for idx, h in enumerate(top_3):
                h.rank = idx + 1
                if not within_budget:
                    h.notes = f"Exceeds target budget cap (${per_night_cap:.2f}/night), but selected as best available option"

            return top_3
