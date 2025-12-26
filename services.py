import json
import os
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

# Load Environment Variables
load_dotenv()

# Setup Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Setup Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- DATA MODELS ---
class Property(BaseModel):
    title: str = Field(description="A catchy 3-5 word title for the listing")
    price: float = Field(description="The numeric price in GHS")
    location_name: str = Field(description="The general neighborhood (e.g., East Legon, Osu)")
    lat: float = Field(description="Latitude coordinate")
    long: float = Field(description="Longitude coordinate")
    type: str = Field(description="Either 'rent' or 'sale'")
    vibe_features: str = Field(description="Comma-separated list of key features (e.g., POOL, GYM, GENERATOR)")
    description: str = Field(description="A 2-sentence marketing summary. Engaging and professional.")
    image_url: Optional[str] = Field(description="URL of the property image if available")

# --- CORE SERVICE: AI EXTRACTION ---
async def process_text_to_property(raw_text: str) -> dict:
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are Asta, an expert Real Estate AI for Accra, Ghana.
    Extract the following listing into structured JSON.
    
    IMPORTANT RULES:
    1. Coordinates: Approximate the lat/long based on the location name if not explicit. 
       - MUST be within Accra (Lat 5.5 to 5.7, Long -0.3 to -0.1).
    2. Currency: Convert USD to GHS (rate: 1 USD = 15 GHS). Return ONLY the number.
    3. Vibe: Extract 3-5 tags (e.g., "POOL", "SECURITY", "MODERN").
    4. Description: Write a compelling 2-sentence summary based on the details.
    
    RAW LISTING:
    {raw_text}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# --- DATABASE SERVICE ---
async def save_to_db(property_data: dict):
    try:
        response = supabase.table('properties').insert(property_data).execute()
        return response.data
    except Exception as e:
        print(f"DB Error: {e}")
        return None
