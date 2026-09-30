from typing import Dict, Optional

# Mapping of canonical 3-letter IATA airport and metro codes to city names
IATA_TO_CITY: Dict[str, str] = {
    # Europe
    "CDG": "Paris",
    "ORY": "Paris",
    "PAR": "Paris",
    "LHR": "London",
    "LGW": "London",
    "STN": "London",
    "LCY": "London",
    "LTN": "London",
    "LON": "London",
    "BER": "Berlin",
    "FRA": "Frankfurt",
    "MUC": "Munich",
    "AMS": "Amsterdam",
    "FCO": "Rome",
    "CIA": "Rome",
    "ROM": "Rome",
    "MXP": "Milan",
    "LIN": "Milan",
    "MIL": "Milan",
    "BCN": "Barcelona",
    "MAD": "Madrid",
    "DUB": "Dublin",
    "VIE": "Vienna",
    "ZRH": "Zurich",
    "GVA": "Geneva",
    "BRU": "Brussels",
    "LIS": "Lisbon",
    "ATH": "Athens",
    "PRG": "Prague",
    "CPH": "Copenhagen",
    "ARN": "Stockholm",
    "OSL": "Oslo",
    "HEL": "Helsinki",
    "BUD": "Budapest",
    "WAW": "Warsaw",
    "EDI": "Edinburgh",
    "IST": "Istanbul",

    # North America
    "JFK": "New York City",
    "EWR": "New York City",
    "LGA": "New York City",
    "NYC": "New York City",
    "LAX": "Los Angeles",
    "SFO": "San Francisco",
    "ORD": "Chicago",
    "MDW": "Chicago",
    "CHI": "Chicago",
    "MIA": "Miami",
    "BOS": "Boston",
    "SEA": "Seattle",
    "LAS": "Las Vegas",
    "MCO": "Orlando",
    "ATL": "Atlanta",
    "DFW": "Dallas",
    "DEN": "Denver",
    "IAH": "Houston",
    "PHX": "Phoenix",
    "IAD": "Washington",
    "DCA": "Washington",
    "WAS": "Washington",
    "YYZ": "Toronto",
    "YVR": "Vancouver",
    "YUL": "Montreal",
    "MEX": "Mexico City",
    "CUN": "Cancun",

    # Asia & Pacific
    "NRT": "Tokyo",
    "HND": "Tokyo",
    "TYO": "Tokyo",
    "KIX": "Osaka",
    "ITM": "Osaka",
    "OSA": "Osaka",
    "ICN": "Seoul",
    "GMP": "Seoul",
    "SEL": "Seoul",
    "SIN": "Singapore",
    "HKG": "Hong Kong",
    "BKK": "Bangkok",
    "DMK": "Bangkok",
    "KUL": "Kuala Lumpur",
    "TPE": "Taipei",
    "SYD": "Sydney",
    "MEL": "Melbourne",
    "BNE": "Brisbane",
    "AKL": "Auckland",
    "BOM": "Mumbai",
    "DEL": "Delhi",
    "BLR": "Bangalore",
    "MAA": "Chennai",
    "CCU": "Kolkata",

    # Middle East & Latin America
    "DXB": "Dubai",
    "DWC": "Dubai",
    "AUH": "Abu Dhabi",
    "DOH": "Doha",
    "TLV": "Tel Aviv",
    "RUH": "Riyadh",
    "JED": "Jeddah",
    "GRU": "Sao Paulo",
    "GIG": "Rio de Janeiro",
    "RIO": "Rio de Janeiro",
    "EZE": "Buenos Aires",
    "BUE": "Buenos Aires",
    "SCL": "Santiago",
    "BOG": "Bogota",
    "LIM": "Lima"
}

# Mapping of city names/aliases to preferred airport IATA code for flight searches
CITY_TO_AIRPORT_IATA: Dict[str, str] = {
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
    "YYZ": "YYZ",
    "FRANKFURT": "FRA",
    "FRA": "FRA",
    "MUNICH": "MUC",
    "MUC": "MUC",
    "MADRID": "MAD",
    "MAD": "MAD",
    "DUBLIN": "DUB",
    "DUB": "DUB",
    "VIENNA": "VIE",
    "VIE": "VIE",
    "ZURICH": "ZRH",
    "ZRH": "ZRH",
    "SEOUL": "ICN",
    "ICN": "ICN",
    "BANGKOK": "BKK",
    "BKK": "BKK",
    "HONG KONG": "HKG",
    "HKG": "HKG",
    "BOSTON": "BOS",
    "BOS": "BOS",
    "SEATTLE": "SEA",
    "SEA": "SEA",
    "LAS VEGAS": "LAS",
    "LAS": "LAS"
}

# Accurate city center coordinates for attraction searches and hotel discovery
CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    # Paris, France
    "PARIS": {"latitude": 48.8566, "longitude": 2.3522},
    "CDG": {"latitude": 48.8566, "longitude": 2.3522},
    "ORY": {"latitude": 48.8566, "longitude": 2.3522},
    "PAR": {"latitude": 48.8566, "longitude": 2.3522},

    # New York City, USA
    "NEW YORK CITY": {"latitude": 40.7128, "longitude": -74.0060},
    "NEW YORK": {"latitude": 40.7128, "longitude": -74.0060},
    "NYC": {"latitude": 40.7128, "longitude": -74.0060},
    "JFK": {"latitude": 40.7128, "longitude": -74.0060},
    "EWR": {"latitude": 40.7128, "longitude": -74.0060},
    "LGA": {"latitude": 40.7128, "longitude": -74.0060},

    # London, United Kingdom
    "LONDON": {"latitude": 51.5074, "longitude": -0.1278},
    "LON": {"latitude": 51.5074, "longitude": -0.1278},
    "LHR": {"latitude": 51.5074, "longitude": -0.1278},
    "LGW": {"latitude": 51.5074, "longitude": -0.1278},
    "STN": {"latitude": 51.5074, "longitude": -0.1278},
    "LCY": {"latitude": 51.5074, "longitude": -0.1278},

    # Tokyo, Japan
    "TOKYO": {"latitude": 35.6762, "longitude": 139.6503},
    "TYO": {"latitude": 35.6762, "longitude": 139.6503},
    "HND": {"latitude": 35.6762, "longitude": 139.6503},
    "NRT": {"latitude": 35.6762, "longitude": 139.6503},

    # Rome, Italy
    "ROME": {"latitude": 41.9028, "longitude": 12.4964},
    "ROM": {"latitude": 41.9028, "longitude": 12.4964},
    "FCO": {"latitude": 41.9028, "longitude": 12.4964},

    # Berlin, Germany
    "BERLIN": {"latitude": 52.5200, "longitude": 13.4050},
    "BER": {"latitude": 52.5200, "longitude": 13.4050},

    # Frankfurt & Munich, Germany
    "FRANKFURT": {"latitude": 50.1109, "longitude": 8.6821},
    "FRA": {"latitude": 50.1109, "longitude": 8.6821},
    "MUNICH": {"latitude": 48.1351, "longitude": 11.5820},
    "MUC": {"latitude": 48.1351, "longitude": 11.5820},

    # Amsterdam, Netherlands
    "AMSTERDAM": {"latitude": 52.3676, "longitude": 4.9041},
    "AMS": {"latitude": 52.3676, "longitude": 4.9041},

    # Barcelona & Madrid, Spain
    "BARCELONA": {"latitude": 41.3879, "longitude": 2.1699},
    "BCN": {"latitude": 41.3879, "longitude": 2.1699},
    "MADRID": {"latitude": 40.4168, "longitude": -3.7038},
    "MAD": {"latitude": 40.4168, "longitude": -3.7038},

    # San Francisco & Los Angeles, USA
    "SAN FRANCISCO": {"latitude": 37.7749, "longitude": -122.4194},
    "SFO": {"latitude": 37.7749, "longitude": -122.4194},
    "LOS ANGELES": {"latitude": 34.0522, "longitude": -118.2437},
    "LAX": {"latitude": 34.0522, "longitude": -118.2437},
    "LA": {"latitude": 34.0522, "longitude": -118.2437},

    # Chicago & Miami, USA
    "CHICAGO": {"latitude": 41.8781, "longitude": -87.6298},
    "ORD": {"latitude": 41.8781, "longitude": -87.6298},
    "CHI": {"latitude": 41.8781, "longitude": -87.6298},
    "MIAMI": {"latitude": 25.7617, "longitude": -80.1918},
    "MIA": {"latitude": 25.7617, "longitude": -80.1918},

    # Boston & Seattle, USA
    "BOSTON": {"latitude": 42.3601, "longitude": -71.0589},
    "BOS": {"latitude": 42.3601, "longitude": -71.0589},
    "SEATTLE": {"latitude": 47.6062, "longitude": -122.3321},
    "SEA": {"latitude": 47.6062, "longitude": -122.3321},
    "LAS VEGAS": {"latitude": 36.1699, "longitude": -115.1398},
    "LAS": {"latitude": 36.1699, "longitude": -115.1398},

    # Sydney & Melbourne, Australia
    "SYDNEY": {"latitude": -33.8688, "longitude": 151.2093},
    "SYD": {"latitude": -33.8688, "longitude": 151.2093},
    "MELBOURNE": {"latitude": -37.8136, "longitude": 144.9631},
    "MEL": {"latitude": -37.8136, "longitude": 144.9631},

    # Singapore & Hong Kong
    "SINGAPORE": {"latitude": 1.3521, "longitude": 103.8198},
    "SIN": {"latitude": 1.3521, "longitude": 103.8198},
    "HONG KONG": {"latitude": 22.3193, "longitude": 114.1694},
    "HKG": {"latitude": 22.3193, "longitude": 114.1694},

    # Dubai, UAE
    "DUBAI": {"latitude": 25.2048, "longitude": 55.2708},
    "DXB": {"latitude": 25.2048, "longitude": 55.2708},

    # India
    "MUMBAI": {"latitude": 19.0760, "longitude": 72.8777},
    "BOM": {"latitude": 19.0760, "longitude": 72.8777},
    "DELHI": {"latitude": 28.6139, "longitude": 77.2090},
    "DEL": {"latitude": 28.6139, "longitude": 77.2090},
    "BANGALORE": {"latitude": 12.9716, "longitude": 77.5946},
    "BLR": {"latitude": 12.9716, "longitude": 77.5946},

    # Toronto, Canada
    "TORONTO": {"latitude": 43.6532, "longitude": -79.3832},
    "YYZ": {"latitude": 43.6532, "longitude": -79.3832},
    "VANCOUVER": {"latitude": 49.2827, "longitude": -123.1207},
    "YVR": {"latitude": 49.2827, "longitude": -123.1207},

    # Seoul, South Korea
    "SEOUL": {"latitude": 37.5665, "longitude": 126.9780},
    "ICN": {"latitude": 37.5665, "longitude": 126.9780},

    # Bangkok, Thailand
    "BANGKOK": {"latitude": 13.7563, "longitude": 100.5018},
    "BKK": {"latitude": 13.7563, "longitude": 100.5018}
}

def resolve_city_name(location: str) -> str:
    """
    Resolves an input location string (which may be a 3-letter IATA airport/metro code
    like CDG, JFK, LHR, NRT, or a city name) to the proper canonical city name.
    E.g. 'CDG' -> 'Paris', 'JFK' -> 'New York', 'LHR' -> 'London', 'NRT' -> 'Tokyo'.
    """
    cleaned = location.strip().upper()
    if cleaned in IATA_TO_CITY:
        return IATA_TO_CITY[cleaned]
    if cleaned in ("NEW YORK", "NYC"):
        return "New York City"
    # Check if cleaned is already a city in CITY_TO_AIRPORT_IATA
    for city_key in CITY_TO_AIRPORT_IATA:
        if cleaned == city_key:
            return city_key.title()
    return location.strip().title()

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
    # If it's an IATA code, map to city name first
    if cleaned in IATA_TO_CITY:
        city_name = IATA_TO_CITY[cleaned].upper()
        if city_name in CITY_COORDINATES:
            return CITY_COORDINATES[city_name]
    # Check partial matching
    for key, coords in CITY_COORDINATES.items():
        if key in cleaned or cleaned in key:
            return coords
    # Default to Paris coordinates as sensible global hub fallback
    return {"latitude": 48.8566, "longitude": 2.3522}
