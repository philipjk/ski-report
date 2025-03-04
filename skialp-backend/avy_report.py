import requests
from bs4 import BeautifulSoup
import openai
import os

# Set your API keys
SERPAPI_KEY = os.getenv('METEOBLUE_API_KEY')
if not SERPAPI_KEY :
    raise ValueError("SERPAPI_KEY environment variable is not set")

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_KEY:
    raise ValueError("OPENAI_KEY environment variable is not set")

# Search Google for the latest avalanche bulletin
def search_avalanche_bulletin(location):
    print(location)
    params = {
        "engine": "google",
        "q": f"{location} avalanche bulletin site:aineva.it",
        "api_key": SERPAPI_KEY
    }
    
    response = requests.get("https://serpapi.com/search", params=params)
    results = response.json()
    
    # Extract the first search result URL
    first_result = results.get("organic_results", [{}])[0].get("link")
    
    return first_result

# Scrape the bulletin content
def get_bulletin_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract text (modify this selector if needed)
    bulletin_text = soup.find("div", class_="bulletin-content")
    
    return bulletin_text.get_text(strip=True) if bulletin_text else "No bulletin found."

# Analyze with GPT
def analyze_bulletin(text):
    prompt = f"Analyze the following avalanche bulletin:\n\n{text}\n\nSummarize the avalanche risk level, snow conditions, and safety recommendations."
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an avalanche risk expert."},
                  {"role": "user", "content": prompt}],
        api_key=OPENAI_KEY
    )
    
    return response["choices"][0]["message"]["content"]

    # Run everything
def avy_risk(country):
    known_sources = {
        "Italy": "https://www.aineva.it",
        "France": "https://www.meteofrance.com",
        "Switzerland": "https://www.slf.ch",
        "Austria": "https://lawinen.at/",
        "USA": "https://www.avalanche.org",
        "Canada": "https://www.avalanche.ca"
    }
    try:
        print(country)
        print(known_sources[country])
        return known_sources[country]
    except:
        return None

    # bulletin_url = search_avalanche_bulletin(location)
    # if bulletin_url:
    #     bulletin_text = get_bulletin_text(bulletin_url)
    #     summary = analyze_bulletin(bulletin_text)
    #     return summary
    # else:
    #     return "No bulletin found."
