from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from unidecode import unidecode
import difflib
from pydantic import BaseModel
import os
import base64
import math
from openai import OpenAI
from avy_report import avy_risk

METEOBLUE_API_KEY = os.getenv('METEOBLUE_API_KEY')
if not METEOBLUE_API_KEY:
    raise ValueError("METEOBLUE_API_KEY environment variable is not set")

# Add OpenAI API key to environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

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
    
    try:
        # Call Nominatim API
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': query,
                'format': 'json',
                'limit': 1,
                'accept-language': 'en'
            },
            headers={'User-Agent': 'SkiAlp/1.0'},
            timeout=10  # Add timeout
        )
        
        if not response.ok:
            return {"error": f"Location service error: {response.status_code}"}
        
        results = response.json()
        
        if not results:
            return {"error": "Location not found. Please try a different location name."}
        
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
    
    except requests.exceptions.Timeout:
        return {"error": "Location service timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to location service. Please check your internet connection."}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

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

def get_nearby_peaks(lat: float, lon: float, radius_km: float = 20):
    """Get peaks within radius_km of the given coordinates"""
    # Calculate bounding box (rough approximation)
    # 1 degree latitude = ~111km
    # 1 degree longitude = ~111km * cos(latitude)
    
    lat_degree = radius_km / 111.0
    lon_degree = radius_km / (111.0 * math.cos(math.radians(float(lat))))
    
    bbox = f"{float(lat)-lat_degree},{float(lon)-lon_degree},{float(lat)+lat_degree},{float(lon)+lon_degree}"
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node
      ["natural"="peak"]
      ({bbox});
    out body;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': query})
        if not response.ok:
            return []
            
        data = response.json()
        peaks = []
        
        for element in data.get('elements', []):
            peaks.append({
                'name': element.get('tags', {}).get('name', 'Unnamed peak'),
                'elevation': element.get('tags', {}).get('ele', 'Unknown'),
                'lat': element.get('lat'),
                'lon': element.get('lon')
            })
        
        # Sort by elevation (if available)
        peaks.sort(key=lambda x: float(x['elevation'].replace('m', '')) if x['elevation'] != 'Unknown' else 0, reverse=True)
        
        # Return top 5 peaks
        return peaks[:6]
        
    except Exception as e:
        print(f"Error fetching peaks: {e}")
        return []

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_meteogram(image_base64: str,
                      snowfall,
                      snow_depth,
                      freezing_level,
                      location) -> str:

    forecasts = f"Snowfall: {snowfall}, Snow-depth: {snow_depth}, Freezing_level: {freezing_level}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """You are a weather analyst, specialized in ski touring."""},
                 
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this meteogram for ski touring conditions
                            for {location}. 
                            The meteogram consists of three panels sharing a common x-axis,
                            representing the forecast for the next few days with time intervals. 
                            The top panel displays temperature trends with a red line,
                            highlighting daily maximum and minimum values. Weather icons 
                            provide general conditions, including precipitation. The middle 
                            panel focuses on cloud coverage at different altitudes, with 
                            particular attention to lower levels (below 5 km), and also 
                            shows precipitation intensity over time. The bottom panel 
                            presents wind data, where the upper line represents wind gusts,
                            the lower line shows average wind speed, and arrows indicate 
                            wind direction. Do NOT comment on precipitation, unless 
                            there is considerable snowing, and snowing only. Provide skialp recommendations considering 
                            the data. Do not use markdown formatting, just use text and newlines.
                            Mention precipitations only when you are absolutely certain and 
                            there are very visible bars in the middle graph.
                            Cloud coverage is absent unless there are wide and 
                            dark spots in the middle graph. Make sure it is a ski-touring 
                            location before saying the conditions for skiing are good.
                            E.g. if the location is Milan, then say it is not a
                            ski location.
                            Current conditions at the base are: {forecasts}.
                            Consider that ski-mountaineers rise in elevation during their tours.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing meteogram: {e}")
        return None

@app.get("/report")
def get_skialp_report(
    location: str = Query(None, description="Location name"),
    lat: float = Query(None, description="Latitude"),
    lon: float = Query(None, description="Longitude")
):
    if not location:
        return {"error": "Please provide a location"}
    
    country = location.split(",")[-1].strip()
    location = location.split(',')[0]
    
    if not lat or not lon:
        # Fallback to geocoding if coordinates aren't provided
        lat, lon = get_coordinates(location)
        if not lat or not lon:
            return {"error": "Location not found. Try a different name."}

    # Fetch weather & snow data
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=snowfall,temperature,snow_depth,freezing_level_height&timezone=auto"
    weather_data = requests.get(weather_url).json()

    freezing_level = weather_data["hourly"]["freezing_level_height"][0]  # Freezing level in meters
    temperature = weather_data["hourly"]["temperature"][0]

    # Get meteogram image   
    meteogram_data = get_meteogram(float(lat), float(lon))
    meteogram_base64 = base64.b64encode(meteogram_data).decode() if meteogram_data else None

    # Get nearby peaks
    nearby_peaks = get_nearby_peaks(lat, lon)

    # Get meteogram analysis
    meteogram_analysis = None
    if meteogram_base64:
        meteogram_analysis = analyze_meteogram(meteogram_base64,
                                               snowfall,
                                               snow_depth,
                                               freezing_level,
                                               location)

    print('do somethings wtf')
    avalanche_risk_url = avy_risk(country)
    print(avalanche_risk_url)

    return {
        "location": location,
        "meteogram": f"data:image/png;base64,{meteogram_base64}" if meteogram_base64 else None,
        "nearby_peaks": nearby_peaks,
        "meteogram_analysis": meteogram_analysis,
        "temperature": temperature,
        "snow_depth": snow_depth,
        "snowfall": snowfall,
        "freezing_level": freezing_level,
        "avalanche_risk": avalanche_risk_url
    }
