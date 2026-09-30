import logging
from typing import List, Optional
from .base import FlightOption, HotelOption, PlaceItem, FlightProvider, HotelProvider, PlacesProvider
from .location import resolve_iata, resolve_coordinates

logger = logging.getLogger("mock_provider")

class MockProvider(FlightProvider, HotelProvider, PlacesProvider):
    """
    Mock data provider for flights, hotels, and attractions used for offline mode,
    testing, or fallback when API keys are unconfigured or live providers error.
    """

    def search_flights(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float
    ) -> List[FlightOption]:
        """Generates realistic top 3 ranked flight options."""
        origin_iata = resolve_iata(origin)
        dest_iata = resolve_iata(destination)
        base_price = max(180.0, round(budget * 0.25, 2)) if budget > 0 else 450.0

        options = [
            FlightOption(
                rank=1,
                id="FL-MOCK-001",
                airline="Delta Air Lines (DL)",
                flight_number="DL 412",
                origin=origin_iata,
                destination=dest_iata,
                departure_time=f"{start_date}T08:30:00",
                arrival_time=f"{start_date}T16:45:00",
                duration="8h 15m",
                stops=0,
                price=round(base_price * 0.9, 2),
                currency="USD",
                source="Mock (Fallback)",
                is_mock=True,
                notes="Best Value non-stop route"
            ),
            FlightOption(
                rank=2,
                id="FL-MOCK-002",
                airline="United Airlines (UA)",
                flight_number="UA 890",
                origin=origin_iata,
                destination=dest_iata,
                departure_time=f"{start_date}T11:15:00",
                arrival_time=f"{start_date}T20:00:00",
                duration="8h 45m",
                stops=1,
                price=round(base_price * 1.05, 2),
                currency="USD",
                source="Mock (Fallback)",
                is_mock=True,
                notes="Flexible cancellation option"
            ),
            FlightOption(
                rank=3,
                id="FL-MOCK-003",
                airline="Air France (AF)",
                flight_number="AF 007",
                origin=origin_iata,
                destination=dest_iata,
                departure_time=f"{start_date}T19:40:00",
                arrival_time=f"{start_date}T09:10:00",
                duration="7h 30m",
                stops=0,
                price=round(base_price * 1.22, 2),
                currency="USD",
                source="Mock (Fallback)",
                is_mock=True,
                notes="Overnight premium direct flight"
            )
        ]

        # Ensure sorted by price ascending and ranked
        sorted_flights = sorted(options, key=lambda f: f.price)
        qualifying_flights = [f for f in sorted_flights if f.price <= budget] if budget > 0 else []
        if qualifying_flights:
            selected_flights = qualifying_flights[:3]
            for f in selected_flights:
                f.notes = f"{f.notes} [within ${budget:.2f} cap]"
            logger.info(
                f"Mock flight search: {len(qualifying_flights)} offers qualify at or under budget cap (${budget:.2f}). "
                f"Selected top {len(selected_flights)} (cheapest: ${selected_flights[0].price:.2f})."
            )
        else:
            selected_flights = sorted_flights[:3]
            if budget > 0:
                for f in selected_flights:
                    f.notes = f"{f.notes} [exceeds ${budget:.2f} cap; cheapest available]"
                cheapest_available = selected_flights[0].price if selected_flights else 0.0
                logger.warning(
                    f"Mock flight search: 0 offers found at or under budget cap (${budget:.2f}). "
                    f"Falling back to {len(selected_flights)} cheapest available offers (lowest: ${cheapest_available:.2f})."
                )

        for i, opt in enumerate(selected_flights):
            opt.rank = i + 1
        return selected_flights

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
        Generates realistic top 3 mock hotel options ranked by rating, then price,
        strictly respecting the per-night lodging budget cap.
        """
        dest_name = destination.strip().title()
        safe_cap = max(20.0, per_night_cap)
        luxury_rate = round(min(safe_cap * 0.95, safe_cap), 2)
        mid_rate = round(safe_cap * 0.72, 2)
        budget_rate = round(safe_cap * 0.50, 2)

        options = [
            HotelOption(
                rank=1,
                id="HTL-MOCK-001",
                name=f"Grand Hotel Le Marais {dest_name}",
                rating=4.9,
                price_per_night=luxury_rate,
                total_price=round(luxury_rate * nights, 2),
                currency="USD",
                link="https://duffel.com/stays/HTL-MOCK-001",
                neighborhood="Central Cultural District",
                amenities=["Free Breakfast", "Spa & Wellness", "High-speed Wi-Fi", "Concierge"],
                source="Mock (Fallback)",
                is_mock=True,
                notes=f"Highest rated accommodation within ${per_night_cap:.2f}/night budget cap"
            ),
            HotelOption(
                rank=2,
                id="HTL-MOCK-002",
                name=f"Boutique Artisan Suites {dest_name}",
                rating=4.7,
                price_per_night=mid_rate,
                total_price=round(mid_rate * nights, 2),
                currency="USD",
                link="https://duffel.com/stays/HTL-MOCK-002",
                neighborhood="Historic Old Town",
                amenities=["Free Wi-Fi", "Espresso Bar", "Bicycle Rental"],
                source="Mock (Fallback)",
                is_mock=True,
                notes="Excellent value boutique property with outstanding guest reviews"
            ),
            HotelOption(
                rank=3,
                id="HTL-MOCK-003",
                name=f"Urban Comfort Living {dest_name}",
                rating=4.5,
                price_per_night=budget_rate,
                total_price=round(budget_rate * nights, 2),
                currency="USD",
                link="https://duffel.com/stays/HTL-MOCK-003",
                neighborhood="Metro & Arts Center",
                amenities=["Free Wi-Fi", "Breakfast Included", "24/7 Front Desk"],
                source="Mock (Fallback)",
                is_mock=True,
                notes="Budget-optimized comfortable stay"
            )
        ]

        # Sort by rating (descending), then price (ascending)
        sorted_hotels = sorted(options, key=lambda h: (-h.rating, h.price_per_night))
        for i, opt in enumerate(sorted_hotels):
            opt.rank = i + 1
        return sorted_hotels

    def fetch_places(
        self,
        destination: str,
        preferences: str = "",
        limit: int = 15
    ) -> List[PlaceItem]:
        """
        Generates realistic candidate attractions, restaurants, and points of interest
        tailored to the destination and traveler preferences.
        """
        dest_title = destination.strip().title()
        coords = resolve_coordinates(destination)
        lat = coords.get("latitude", 48.8566)
        lon = coords.get("longitude", 2.3522)

        items = [
            PlaceItem(
                id="PLC-MOCK-001",
                name=f"{dest_title} National Art Gallery & Modern Masters",
                category="Museum & Art",
                address=f"10 Museum Way, Central District, {dest_title}",
                rating=4.9,
                coordinates={"latitude": round(lat + 0.005, 4), "longitude": round(lon + 0.004, 4)},
                types=["museum", "art_gallery", "tourist_attraction"],
                estimated_cost=25.0,
                description=f"Premier art institution featuring classic and contemporary masterpieces in {dest_title}.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-002",
                name=f"Historic Old Quarter & Cathedral Plaza",
                category="Sightseeing & Culture",
                address=f"Place Royale, Historic Center, {dest_title}",
                rating=4.8,
                coordinates={"latitude": round(lat - 0.003, 4), "longitude": round(lon - 0.002, 4)},
                types=["tourist_attraction", "historical_landmark"],
                estimated_cost=15.0,
                description=f"Centuries-old cobblestone plaza surrounded by baroque architecture and street performers.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-003",
                name=f"Grand Artisan Food Market & Tasting Hall",
                category="Food & Culinary",
                address=f"24 Gourmet Blvd, River Quarter, {dest_title}",
                rating=4.85,
                coordinates={"latitude": round(lat + 0.008, 4), "longitude": round(lon - 0.005, 4)},
                types=["food", "restaurant", "market"],
                estimated_cost=45.0,
                description=f"Vibrant market stalls serving local cheeses, wines, pastries, and regional delicacies.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-004",
                name=f"{dest_title} Panoramic Sky Observation Deck",
                category="Landmark & Views",
                address=f"Tower 1, Skyline Promenade, {dest_title}",
                rating=4.7,
                coordinates={"latitude": round(lat - 0.007, 4), "longitude": round(lon + 0.006, 4)},
                types=["tourist_attraction", "point_of_interest"],
                estimated_cost=35.0,
                description=f"360-degree panoramic glass terrace overlooking the entire cityscape of {dest_title}.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-005",
                name=f"Royal Botanical Gardens & Sculpture Pavilion",
                category="Park & Nature",
                address=f"Parkland Avenue, Garden District, {dest_title}",
                rating=4.75,
                coordinates={"latitude": round(lat + 0.012, 4), "longitude": round(lon + 0.001, 4)},
                types=["park", "tourist_attraction"],
                estimated_cost=12.0,
                description="Tranquil shaded walkways, rare flora exhibits, and classical marble sculptures.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-006",
                name=f"Chef's Heritage Bistro & Wine Bar",
                category="Food & Culinary",
                address=f"8 Rue Gastronomique, {dest_title}",
                rating=4.9,
                coordinates={"latitude": round(lat - 0.002, 4), "longitude": round(lon + 0.003, 4)},
                types=["restaurant", "food"],
                estimated_cost=55.0,
                description="Acclaimed farm-to-table cuisine celebrating traditional recipes with modern finesse.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-007",
                name=f"{dest_title} Riverside Promenade & Sunset Cruise",
                category="Tour & Experience",
                address=f"Pier 4, Grand Embankment, {dest_title}",
                rating=4.8,
                coordinates={"latitude": round(lat + 0.003, 4), "longitude": round(lon - 0.008, 4)},
                types=["tourist_attraction", "tour"],
                estimated_cost=40.0,
                description="Scenic guided river boat cruise admiring illuminated architectural monuments at dusk.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-008",
                name=f"Contemporary Sculpture Park & Design Museum",
                category="Museum & Art",
                address=f"15 Bauhaus Way, Arts District, {dest_title}",
                rating=4.65,
                coordinates={"latitude": round(lat + 0.010, 4), "longitude": round(lon + 0.009, 4)},
                types=["museum", "art_gallery"],
                estimated_cost=20.0,
                description="Cutting-edge contemporary exhibitions, interactive installations, and design cafe.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-009",
                name=f"Historic Citadel & Fortress Ramparts",
                category="Sightseeing & Culture",
                address=f"Citadel Hill, Old Fortress Road, {dest_title}",
                rating=4.7,
                coordinates={"latitude": round(lat - 0.015, 4), "longitude": round(lon - 0.010, 4)},
                types=["historical_landmark", "tourist_attraction"],
                estimated_cost=18.0,
                description="Medieval stronghold offering walking ramparts, historical armory, and scenic views.",
                source="Mock (Fallback)",
                is_mock=True
            ),
            PlaceItem(
                id="PLC-MOCK-010",
                name=f"Twilight Street Food Tour & Speakeasy Walk",
                category="Food & Culinary",
                address=f"Lantern Alley, {dest_title}",
                rating=4.95,
                coordinates={"latitude": round(lat - 0.004, 4), "longitude": round(lon + 0.007, 4)},
                types=["food", "tour"],
                estimated_cost=50.0,
                description="Guided evening walking tour tasting 5 signature street food bites and craft beverages.",
                source="Mock (Fallback)",
                is_mock=True
            )
        ]

        # Prioritize places matching preferences
        pref_lower = (preferences or "").lower()
        if pref_lower:
            keywords = [w for w in pref_lower.replace(",", " ").split() if len(w) > 3]
            if keywords:
                def score_pref(p: PlaceItem) -> int:
                    s = 0
                    text = f"{p.name} {p.category} {p.description or ''}".lower()
                    for kw in keywords:
                        if kw in text:
                            s += 1
                    return s
                items = sorted(items, key=lambda p: (-score_pref(p), -p.rating))

        return items[:limit]
