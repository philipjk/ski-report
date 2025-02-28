from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Enable CORS (for frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LAT, LON = 45.9237, 6.8694  # Example location (Chamonix)

@app.get("/report")  # Ensure this route is correctly defined
def get_skialp_report():
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m,snow_depth"
    weather_data = requests.get(weather_url).json()

    return {
        "location": "Chamonix, France",
        "temperature": weather_data["hourly"]["temperature_2m"][0],
        "snow_depth": weather_data["hourly"]["snow_depth"][0],
        "avalanche_risk": "Moderate"
    }