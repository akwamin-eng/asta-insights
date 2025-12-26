import os
import json
import time
from supabase import create_client, Client
from google import genai
from google.genai import types
import googlemaps

# 1. SETUP & AUTH
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Must use Service Role to edit data
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_MAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY, GOOGLE_MAPS_KEY]):
    print("❌ Missing API Keys. Check your .env or Secrets.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
client = genai.Client(api_key=GOOGLE_API_KEY)

def clean_text_with_ai(raw_location, raw_desc, raw_features):
    """Uses Gemini to extract structured data from messy WhatsApp text."""
    
    prompt = f"""
    You are a Ghana Real Estate Data Expert. Analyze this raw listing data:
    
    Raw Location Input: "{raw_location}"
    Raw Description/Details: "{raw_desc}"
    Raw Amenities/Vibe: "{raw_features}"

    Your Goal:
    1. Extract the specific Neighborhood/Suburb name for Geocoding (e.g., "Teshie-Nungua Estates", "Achimota").
    2. Extract a clean list of amenities (e.g., ["Solar", "Security", "Pool"]).
    3. Write a professional 2-sentence description.

    Return ONLY JSON in this format:
    {{
      "clean_location_for_geocoding": "String",
      "display_location_name": "String",
      "amenities_list": ["String", "String"],
      "professional_description": "String"
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ AI Parsing failed: {e}")
        return None

def get_coordinates(address):
    """Gets strict Lat/Long from Google Maps."""
    try:
        # Append 'Ghana' to ensure we don't end up in other countries
        geocode_result = gmaps.geocode(f"{address}, Accra, Ghana")
        
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            formatted_address = geocode_result[0]['formatted_address']
            return location['lat'], location['lng'], formatted_address
        return 0, 0, None
    except Exception as e:
        print(f"⚠️ Geocoding failed: {e}")
        return 0, 0, None

def run_sanitizer():
    print("🧹 Starting Asta Data Sanitizer...")
    
    # 1. Find 'Bad' Listings (Ocean coordinates OR Unprocessed text)
    # We look for listings updated recently to fix the WhatsApp imports
    response = supabase.table('properties').select('*').or_('lat.eq.0,lat.is.null').execute()
    bad_listings = response.data

    print(f"found {len(bad_listings)} listings to fix.")

    for listing in bad_listings:
        print(f"\nProcessing ID {listing['id']}: {listing['title']}...")

        # 2. AI Parsing
        ai_data = clean_text_with_ai(
            listing.get('location_name', ''), 
            listing.get('description', '') or listing.get('details', ''),
            listing.get('vibe_features', '')
        )

        if not ai_data:
            continue

        clean_loc = ai_data['clean_location_for_geocoding']
        print(f"   📍 AI identified location: {clean_loc}")

        # 3. Geocoding
        lat, lng, formatted_address = get_coordinates(clean_loc)
        
        if lat == 0:
            print("   ❌ Could not geocode. Skipping.")
            continue
            
        print(f"   🌍 Found Coordinates: {lat}, {lng} ({formatted_address})")

        # 4. Update Database
        update_payload = {
            "location_name": ai_data['display_location_name'],
            "location_address": formatted_address,
            "lat": lat,
            "long": lng,
            "vibe_features": json.dumps(ai_data['amenities_list']), # Save as JSON array
            "description_enriched": ai_data['professional_description'],
            "location_accuracy": "high"
        }

        supabase.table('properties').update(update_payload).eq('id', listing['id']).execute()
        print("   ✅ Listing Updated in Vault.")
        
        # Respect API limits
        time.sleep(1)

if __name__ == "__main__":
    run_sanitizer()
