from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to convert location name to coordinates
def get_coordinates(location: str):
    geo_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
    response = requests.get(geo_url).json()
    
    if not response:
        return None, None  # Location not found
    
    lat = response[0]["lat"]
    lon = response[0]["lon"]
    return lat, lon

@app.get("/report")
def get_skialp_report(location: str = Query(..., description="Location name")):
    lat, lon = get_coordinates(location)
    
    if not lat or not lon:
        return {"error": "Location not found. Try a different name."}

    # Fetch weather & snow data
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,snow_depth"
    weather_data = requests.get(weather_url).json()

    return {
        "location": location.title(),
        "temperature": weather_data["hourly"]["temperature_2m"][0],
        "snow_depth": weather_data["hourly"]["snow_depth"][0],
        "avalanche_risk": "Moderate",  # Placeholder
        "summary": f"Conditions in {location.title()} seem stable. Check avalanche forecasts before planning a tour."
    }
