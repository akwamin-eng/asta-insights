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

def geocode_address(address):
    if not isinstance(address, str) or pd.isna(address):
        return None, None
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": f"{address}, Ghana",
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10).json()
        if response["status"] == "OK" and len(response["results"]) > 0:
            loc = response["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
        else:
            return None, None  # Skip failed
    except Exception:
        return None, None

# Load data
df = pd.read_csv("ghana_properties_with_predictions.csv")
total = len(df)
success = 0

print(f"🌍 Geocoding {total} addresses... (this may take 5-10 minutes)")

for idx in df.index:
    address = df.loc[idx, "address"]
    lat, lng = geocode_address(address)
    
    if lat is not None:
        df.loc[idx, "latitude"] = lat
        df.loc[idx, "longitude"] = lng
        success += 1
    
    if idx % 50 == 0:
        print(f"  Progress: {idx}/{total} | Success: {success}")
    
    time.sleep(0.1)  # Stay under quota

df.to_csv("ghana_properties_geocoded_full.csv", index=False)
print(f"\n✅ Geocoding complete! {success}/{total} succeeded.")
print("💾 Saved to 'ghana_properties_geocoded_full.csv'")