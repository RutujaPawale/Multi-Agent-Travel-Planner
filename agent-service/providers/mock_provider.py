import logging
from typing import List, Optional
from .base import FlightOption, HotelOption, FlightProvider, HotelProvider
from .location import resolve_iata

logger = logging.getLogger("mock_provider")

class MockProvider(FlightProvider, HotelProvider):
    """
    Mock data provider for flights and hotels used for offline mode,
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
        for i, opt in enumerate(sorted_flights):
            opt.rank = i + 1
        return sorted_flights

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
        safe_cap = max(60.0, per_night_cap)
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
