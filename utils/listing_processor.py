import os
import json
from supabase import create_client
from google import genai
from google.genai import types
import googlemaps

# Initialize Clients (Reuse the env vars you just set up)
supabase = create_client(
    os.environ.get("SUPABASE_URL"), 
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)
gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def process_and_save_listing(phone_number, raw_data):
    """
    Takes raw session data from the bot, cleans it with AI, 
    geocodes it, and saves it to the 'properties' table.
    """
    print(f"🧠 Processing listing for {phone_number}...")

    # 1. AI CLEANING
    prompt = f"""
    Analyze this raw real estate input from WhatsApp:
    Location: "{raw_data.get('location', '')}"
    Details: "{raw_data.get('details', '')}"
    Vibe: "{raw_data.get('vibe', '')}"
    Price: "{raw_data.get('price', '')}"
    Type: "{raw_data.get('type', 'rent')}"

    Tasks:
    1. Extract a precise location name for geocoding.
    2. Format the price as a number (remove currency symbols).
    3. Extract a list of amenity tags.
    4. Write a professional description.

    Return JSON:
    {{
      "clean_location": "String",
      "price_numeric": 0.0,
      "amenities": ["tag1", "tag2"],
      "description": "String"
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        ai_result = json.loads(response.text)
    except Exception as e:
        print(f"❌ AI Error: {e}")
        # Fallback: Save raw data if AI fails
        ai_result = {
            "clean_location": raw_data.get('location'),
            "price_numeric": 0,
            "amenities": [],
            "description": raw_data.get('details')
        }

    # 2. GEOCODING (The Anchor)
    lat, lng, address = 0, 0, "Unmapped"
    try:
        geocode = gmaps.geocode(f"{ai_result['clean_location']}, Accra, Ghana")
        if geocode:
            loc = geocode[0]['geometry']['location']
            lat, lng = loc['lat'], loc['lng']
            address = geocode[0]['formatted_address']
    except Exception as e:
        print(f"❌ Geocode Error: {e}")

    # 3. SAVE TO DB (The Trust Vault)
    # We use the 'upsert' method to create the listing
    payload = {
        "title": f"{raw_data.get('type', 'Property').title()} in {ai_result['clean_location']}",
        "price": ai_result['price_numeric'],
        "location_name": ai_result['clean_location'],
        "location_address": address,
        "lat": lat,
        "long": lng,
        "type": raw_data.get('type', 'rent').lower(),
        "description_enriched": ai_result['description'],
        "vibe_features": json.dumps(ai_result['amenities']),
        "contact_phone": phone_number,
        "source": "whatsapp_bot",
        "status": "active",
        "cover_image_url": raw_data.get('image_url') # The new column we added!
    }

    data, count = supabase.table('properties').insert(payload).execute()
    return data
