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

class PlaceItem(BaseModel):
    """Raw or normalized place item retrieved from OpenTripMap or Mock source."""
    id: str
    name: str
    category: str
    address: Optional[str] = None
    rating: Optional[float] = 4.5
    coordinates: Optional[Dict[str, float]] = None
    types: Optional[List[str]] = None
    estimated_cost: Optional[float] = 30.0
    description: Optional[str] = None
    source: str = "Live API"
    is_mock: bool = False

class ActivityOption(BaseModel):
    """Individual scheduled activity in the day-by-day travel plan."""
    id: str
    name: str
    category: str
    estimated_cost: float
    currency: str = "USD"
    day: int = 1
    time_slot: Optional[str] = "Morning"  # e.g. "Morning", "Afternoon", "Evening"
    duration: Optional[str] = "2-3 hours"
    rating: Optional[float] = 4.5
    description: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    source: str = "OpenTripMap API"
    is_mock: bool = False

class DayPlan(BaseModel):
    """Structured itinerary plan for a single day of the trip."""
    day: int
    theme: Optional[str] = None
    estimated_daily_cost: float = 0.0
    activities: List[ActivityOption] = Field(default_factory=list)

class DayByDayPlan(BaseModel):
    """Full multi-day itinerary plan containing structured daily activities."""
    days: List[DayPlan] = Field(default_factory=list)
    summary: Optional[str] = None

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

class PlacesProvider(ABC):
    """Abstract interface for place/attraction search providers (e.g. OpenTripMap)."""

    @abstractmethod
    def fetch_places(
        self,
        destination: str,
        preferences: str = "",
        limit: int = 15
    ) -> List[PlaceItem]:
        """Fetch candidate attractions, restaurants, and points of interest for a destination."""
        pass
