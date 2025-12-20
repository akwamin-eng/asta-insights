import os
import time
import re
from dotenv import load_dotenv
from supabase import create_client
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# 1. SETUP & CONFIGURATION
if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing Supabase credentials.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Geocoder with a unique user agent for Nominatim (Required by policy)
geolocator = Nominatim(user_agent="asta_ghana_real_estate_v2")

def clean_location(raw_text):
    """
    Strips 'noise' from listing titles to extract the neighborhood name.
    Example: '5 bedroom house for sale in Kwabenya' -> 'Kwabenya'
    """
    if not raw_text:
        return "Accra"
    
    # Logic: Look for the word 'in ' and take everything after it
    match = re.search(r'in\s+(.+)', raw_text, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        # Remove trailing noise like '- Shiashie' or '(near Special Gardens)'
        location = re.split(r'[-\(]', location)[0].strip()
        return location
    
    # Fallback: If 'in' isn't present, take the first 40 characters
    return raw_text[:40].strip()

def run_geocoding():
    print("🌍 Starting Neighborhood Geocoding Loop...")
    
    # 2. FETCH DATA
    # We only look for unique locations in the heatmap table missing coordinates
    try:
        res = supabase.table("market_insights") \
            .select("location") \
            .is_("latitude", "null") \
            .execute()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    if not res.data:
        print("✅ No missing coordinates found in market_insights.")
        return

    # 3. PROCESSING LOOP
    for item in res.data:
        raw_name = item['location']
        
        # Clean the title to get just the neighborhood (e.g., 'Tse Addo')
        loc_name = clean_location(raw_name)
        
        # Force the search to stay in Accra, Ghana
        query = f"{loc_name}, Accra, Ghana"
        print(f"📍 Geocoding: {query}...")
        
        try:
            # Attempt to find coordinates
            location = geolocator.geocode(query, timeout=10)
            
            if location:
                # Update the database
                supabase.table("market_insights").update({
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }).eq("location", raw_name).execute()
                print(f"   ✅ Success: {location.latitude}, {location.longitude}")
            else:
                print(f"   ⚠️ Result not found for: {loc_name}")
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"   ❌ Service Error for {loc_name}: {e}")
            time.sleep(2) # Give the service a breather
            
        # 4. RATE LIMITING
        # Nominatim policy requires absolute max 1 request per second
        time.sleep(1.2)

if __name__ == "__main__":
    run_geocoding()
