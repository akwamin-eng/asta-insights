import os
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path('.') / '.env')
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

if not API_KEY:
    raise EnvironmentError("❌ Missing GOOGLE_PLACES_API_KEY in .env")

def get_poi_count(lat, lng, place_type, radius=1500):
    """Get number of places near coordinates."""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": place_type,
        "key": API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10).json()
        return len(response.get("results", []))
    except Exception:
        return 0

# Load geocoded data
df = pd.read_csv("ghana_properties_geocoded_full.csv")
total = len(df)
print(f"📍 Enriching {total} properties with POIs...")

for idx in df.index:
    lat = df.loc[idx, "latitude"]
    lng = df.loc[idx, "longitude"]
    
    # Skip if coordinates are missing
    if pd.isna(lat) or pd.isna(lng):
        df.loc[idx, "schools_nearby"] = 0
        df.loc[idx, "hospitals_nearby"] = 0
        df.loc[idx, "malls_nearby"] = 0
        df.loc[idx, "transit_nearby"] = 0
        continue
    
    schools = get_poi_count(lat, lng, "school")
    hospitals = get_poi_count(lat, lng, "hospital")
    malls = get_poi_count(lat, lng, "shopping_mall")
    transit = get_poi_count(lat, lng, "transit_station")
    
    df.loc[idx, "schools_nearby"] = schools
    df.loc[idx, "hospitals_nearby"] = hospitals
    df.loc[idx, "malls_nearby"] = malls
    df.loc[idx, "transit_nearby"] = transit
    
    if idx % 100 == 0:
        print(f"  Progress: {idx}/{total}")
    
    time.sleep(0.1)  # Respect rate limits

df.to_csv("ghana_properties_poi_enriched.csv", index=False)
print("\n✅ POI enrichment complete!")
print("💾 Saved to 'ghana_properties_poi_enriched.csv'")