from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class FlightOption(BaseModel):
    id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration: str
    stops: int = 0
    price: float
    currency: str = "USD"
    rank: Optional[int] = None
    source: str = "Live API"
    is_mock: bool = False
    notes: Optional[str] = None

class HotelOption(BaseModel):
    id: str
    name: str
    rating: float = 4.0
    price_per_night: float
    total_price: float
    currency: str = "USD"
    rank: Optional[int] = None
    link: Optional[str] = None
    neighborhood: Optional[str] = None
    amenities: Optional[List[str]] = None
    source: str = "Live API"
    is_mock: bool = False
    notes: Optional[str] = None

class FlightProvider(ABC):
    """Abstract interface for flight search providers."""

    @abstractmethod
    def search_flights(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float
    ) -> List[FlightOption]:
        """Search flights and return normalized FlightOption models."""
        pass

class HotelProvider(ABC):
    """Abstract interface for hotel / accommodation search providers."""

    @abstractmethod
    def search_hotels(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        per_night_cap: float,
        nights: int
    ) -> List[HotelOption]:
        """Search hotels and return normalized HotelOption models."""
        pass
