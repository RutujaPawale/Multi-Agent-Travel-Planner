from typing import Dict

CITY_TO_AIRPORT_IATA = {
    "NEW YORK": "JFK",
    "NYC": "JFK",
    "JFK": "JFK",
    "EWR": "EWR",
    "LGA": "LGA",
    "LOS ANGELES": "LAX",
    "LA": "LAX",
    "LAX": "LAX",
    "SAN FRANCISCO": "SFO",
    "SFO": "SFO",
    "LONDON": "LHR",
    "LON": "LHR",
    "LHR": "LHR",
    "LGW": "LGW",
    "PARIS": "CDG",
    "PAR": "CDG",
    "CDG": "CDG",
    "ORY": "ORY",
    "TOKYO": "HND",
    "TYO": "HND",
    "HND": "HND",
    "NRT": "NRT",
    "BERLIN": "BER",
    "BER": "BER",
    "ROME": "FCO",
    "ROM": "FCO",
    "FCO": "FCO",
    "SYDNEY": "SYD",
    "SYD": "SYD",
    "SINGAPORE": "SIN",
    "SIN": "SIN",
    "DUBAI": "DXB",
    "DXB": "DXB",
    "MUMBAI": "BOM",
    "BOM": "BOM",
    "DELHI": "DEL",
    "DEL": "DEL",
    "AMSTERDAM": "AMS",
    "AMS": "AMS",
    "BARCELONA": "BCN",
    "BCN": "BCN",
    "CHICAGO": "ORD",
    "ORD": "ORD",
    "MIAMI": "MIA",
    "MIA": "MIA",
    "TORONTO": "YYZ",
    "YYZ": "YYZ"
}

CITY_COORDINATES = {
    "PARIS": {"latitude": 48.8566, "longitude": 2.3522},
    "CDG": {"latitude": 48.8566, "longitude": 2.3522},
    "PAR": {"latitude": 48.8566, "longitude": 2.3522},
    "NEW YORK": {"latitude": 40.7128, "longitude": -74.0060},
    "NYC": {"latitude": 40.7128, "longitude": -74.0060},
    "JFK": {"latitude": 40.6413, "longitude": -73.7781},
    "EWR": {"latitude": 40.6895, "longitude": -74.1745},
    "LONDON": {"latitude": 51.5074, "longitude": -0.1278},
    "LON": {"latitude": 51.5074, "longitude": -0.1278},
    "LHR": {"latitude": 51.4700, "longitude": -0.4543},
    "LGW": {"latitude": 51.1537, "longitude": -0.1821},
    "TOKYO": {"latitude": 35.6762, "longitude": 139.6503},
    "TYO": {"latitude": 35.6762, "longitude": 139.6503},
    "HND": {"latitude": 35.5494, "longitude": 139.7798},
    "ROME": {"latitude": 41.9028, "longitude": 12.4964},
    "FCO": {"latitude": 41.8003, "longitude": 12.2389},
    "BERLIN": {"latitude": 52.5200, "longitude": 13.4050},
    "BER": {"latitude": 52.3667, "longitude": 13.5033},
    "SAN FRANCISCO": {"latitude": 37.7749, "longitude": -122.4194},
    "SFO": {"latitude": 37.6213, "longitude": -122.3790},
    "LOS ANGELES": {"latitude": 34.0522, "longitude": -118.2437},
    "LAX": {"latitude": 33.9416, "longitude": -118.4085},
    "SINGAPORE": {"latitude": 1.3521, "longitude": 103.8198},
    "SIN": {"latitude": 1.3644, "longitude": 103.9915},
    "DUBAI": {"latitude": 25.2048, "longitude": 55.2708},
    "DXB": {"latitude": 25.2532, "longitude": 55.3657},
    "MUMBAI": {"latitude": 19.0760, "longitude": 72.8777},
    "BOM": {"latitude": 19.0896, "longitude": 72.8656},
    "DELHI": {"latitude": 28.6139, "longitude": 77.2090},
    "DEL": {"latitude": 28.5562, "longitude": 77.1000},
    "AMSTERDAM": {"latitude": 52.3676, "longitude": 4.9041},
    "AMS": {"latitude": 52.3105, "longitude": 4.7683},
    "BARCELONA": {"latitude": 41.3879, "longitude": 2.1699},
    "BCN": {"latitude": 41.2974, "longitude": 2.0833},
    "CHICAGO": {"latitude": 41.8781, "longitude": -87.6298},
    "ORD": {"latitude": 41.9742, "longitude": -87.9073},
    "MIAMI": {"latitude": 25.7617, "longitude": -80.1918},
    "MIA": {"latitude": 25.7959, "longitude": -80.2870},
    "SYDNEY": {"latitude": -33.8688, "longitude": 151.2093},
    "SYD": {"latitude": -33.9399, "longitude": 151.1753},
    "TORONTO": {"latitude": 43.6532, "longitude": -79.3832},
    "YYZ": {"latitude": 43.6777, "longitude": -79.6248}
}

def resolve_iata(location: str) -> str:
    """Resolves an origin/destination string to a 3-letter airport or city IATA code."""
    cleaned = location.strip().upper()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned
    return CITY_TO_AIRPORT_IATA.get(cleaned, cleaned[:3].upper() if len(cleaned) >= 3 else "JFK")

def resolve_coordinates(location: str) -> Dict[str, float]:
    """Resolves a destination city or airport to geographic coordinates."""
    cleaned = location.strip().upper()
    if cleaned in CITY_COORDINATES:
        return CITY_COORDINATES[cleaned]
    # Check partial matching
    for key, coords in CITY_COORDINATES.items():
        if key in cleaned or cleaned in key:
            return coords
    # Default to Paris coordinates as sensible global hub fallback
    return {"latitude": 48.8566, "longitude": 2.3522}
