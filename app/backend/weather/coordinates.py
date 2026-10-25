"""Representative coordinates and geographic metadata for Kerala districts.

NASA POWER provides gridded meteorological parameters on a 0.5 x 0.5 degree
resolution grid. These coordinates represent geographic centroids / administrative
centers for each district.
"""

from typing import Dict, Any


KERALA_DISTRICT_COORDINATES: Dict[str, Dict[str, Any]] = {
    "Thiruvananthapuram": {
        "latitude": 8.5241,
        "longitude": 76.9366,
        "elevation_m": 16,
        "region": "South Kerala Coastal/Midland",
        "description": "State capital, southern coastal lowlands and undulating midlands.",
    },
    "Kollam": {
        "latitude": 8.8932,
        "longitude": 76.6141,
        "elevation_m": 15,
        "region": "South Kerala Coastal/Midland",
        "description": "Ashtamudi basin, cashew and spice belt.",
    },
    "Pathanamthitta": {
        "latitude": 9.2648,
        "longitude": 76.7870,
        "elevation_m": 19,
        "region": "Central Travancore Foothills",
        "description": "Forested highlands, rubber plantations, and Pamba river basin.",
    },
    "Alappuzha": {
        "latitude": 9.4981,
        "longitude": 76.3388,
        "elevation_m": 1,
        "region": "Kuttanad Lowlands",
        "description": "Below-sea-level rice polders and backwater agro-ecosystem.",
    },
    "Kottayam": {
        "latitude": 9.5916,
        "longitude": 76.5222,
        "elevation_m": 12,
        "region": "Central Midlands",
        "description": "Rubber, spice, and tapioca cultivating midland tract.",
    },
    "Idukki": {
        "latitude": 9.8494,
        "longitude": 76.9710,
        "elevation_m": 750,
        "region": "High Ranges (Western Ghats)",
        "description": "Mountainous district; cardamom, pepper, and tea plantations.",
    },
    "Ernakulam": {
        "latitude": 9.9816,
        "longitude": 76.2999,
        "elevation_m": 4,
        "region": "Central Coastal & Alluvial Plains",
        "description": "Commercial hub, Periyar river basin, Pokkali tidal tracts.",
    },
    "Thrissur": {
        "latitude": 10.5276,
        "longitude": 76.2144,
        "elevation_m": 2.8,
        "region": "Central Lowlands & Kole Lands",
        "description": "Kole wetland paddy fields and midland mixed cropping.",
    },
    "Palakkad": {
        "latitude": 10.7867,
        "longitude": 76.6548,
        "elevation_m": 84,
        "region": "Palakkad Gap Agrarian Basin",
        "description": "Rice granary of Kerala; semi-arid microclimate with higher summer temperatures.",
    },
    "Malappuram": {
        "latitude": 11.0735,
        "longitude": 76.0740,
        "elevation_m": 28,
        "region": "North-Central Midland",
        "description": "Lateritic hills, coconut groves, and arecanut valleys.",
    },
    "Kozhikode": {
        "latitude": 11.2588,
        "longitude": 75.7804,
        "elevation_m": 1,
        "region": "North Malabar Coast",
        "description": "Historic Malabar coast; high rainfall maritime climate.",
    },
    "Wayanad": {
        "latitude": 11.6103,
        "longitude": 76.0827,
        "elevation_m": 780,
        "region": "Wayanad Plateau (Western Ghats)",
        "description": "High-altitude coffee, pepper, and specialty paddy zone.",
    },
    "Kannur": {
        "latitude": 11.8745,
        "longitude": 75.3704,
        "elevation_m": 16,
        "region": "North Malabar",
        "description": "Coastal and lateritic midlands; cashew, rubber, and Kaipad wetland paddy.",
    },
    "Kasaragod": {
        "latitude": 12.5102,
        "longitude": 74.9852,
        "elevation_m": 19,
        "region": "Northernmost Coastal & Laterite Plateau",
        "description": "Heavy monsoon coastal tract, laterite plateaus, and arecanut plantations.",
    },
}
