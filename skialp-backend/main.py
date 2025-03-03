from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from unidecode import unidecode
import difflib
from pydantic import BaseModel
import os
import base64

METEOBLUE_API_KEY = os.getenv('METEOBLUE_API_KEY')
if not METEOBLUE_API_KEY:
    raise ValueError("METEOBLUE_API_KEY environment variable is not set")

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LocationQuery(BaseModel):
    query: str

@app.post("/validate-location")
async def validate_location(location_query: LocationQuery):
    query = location_query.query.strip()
    
    if not query:
        return {"error": "Please enter a location"}
    
    # Normalize the query (remove accents, convert to lowercase)
    normalized_query = unidecode(query.lower())
    
    # Call Nominatim API
    response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={
            'q': query,
            'format': 'json',
            'limit': 1,
            'accept-language': 'en'
        },
        headers={'User-Agent': 'SkiAlp/1.0'}
    )
    
    if not response.ok:
        return {"error": "Location service unavailable"}
    
    results = response.json()
    
    if not results:
        return {"error": "Location not found"}
    
    result = results[0]
    
    # Create a normalized version of the found location name
    normalized_result = unidecode(result['display_name'].lower())
    
    # Calculate similarity between input and result
    similarity = difflib.SequenceMatcher(None, normalized_query, normalized_result).ratio()
    
    location_data = {
        'name': result['display_name'],
        'lat': float(result['lat']),
        'lon': float(result['lon']),
        'original_query': query
    }
    
    return {"location": location_data}

# Function to convert location name to coordinates
def get_coordinates(location: str):
    geo_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
    response = requests.get(geo_url).json()
    
    if not response:
        return None, None  # Location not found
    
    lat = response[0]["lat"]
    lon = response[0]["lon"]
    return lat, lon


def get_meteogram(lat: float, lon: float):
    meteogram_url = f"https://my.meteoblue.com/images/meteogram"
    params = {
        'lat': lat,
        'lon': lon,
        'apikey': METEOBLUE_API_KEY,
        'type': 'classical',
        'temperature': 'C',
        'windspeed': 'kmh',
        'winddirection': 'degree',
        'precipitationamount': 'mm',
        'format': 'png'
    }
    response = requests.get(meteogram_url, params=params)
    if response.ok:
        return response.content  # Returns the binary image data
    return None


@app.get("/report")
def get_skialp_report(
    location: str = Query(None, description="Location name"),
    lat: float = Query(None, description="Latitude"),
    lon: float = Query(None, description="Longitude")
):
    if not location:
        return {"error": "Please provide a location"}
    
    if not lat or not lon:
        # Fallback to geocoding if coordinates aren't provided
        lat, lon = get_coordinates(location)
        if not lat or not lon:
            return {"error": "Location not found. Try a different name."}

    # Fetch weather & snow data
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,snow_depth"
    weather_data = requests.get(weather_url).json()

    # Get first non-null snow depth value, or 0 if none found
    snow_depths = weather_data["hourly"]["snow_depth"]
    snow_depth = next((depth for depth in snow_depths if depth is not None), 0)

    # Get meteogram image   
    meteogram_data = get_meteogram(float(lat), float(lon))
    meteogram_base64 = base64.b64encode(meteogram_data).decode() if meteogram_data else None

    return {
        "location": location,
        "temperature": round(weather_data["hourly"]["temperature_2m"][0], 1),
        "snow_depth": round(snow_depth, 1),
        "avalanche_risk": "Moderate",
        "summary": f"Conditions in {location} seem stable. Check avalanche forecasts before planning a tour.",
        "meteogram": f"data:image/png;base64,{meteogram_base64}" if meteogram_base64 else None
    }
