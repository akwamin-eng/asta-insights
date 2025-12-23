import os
import json
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai import types
from urllib.parse import quote

# Import GPS Utility
from api.utils import extract_gps_from_file

# Load environment variables
load_dotenv()

# Initialize Clients
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# --- APP CONFIGURATION ---
app = FastAPI(
    title="Asta Insights API",
    description="The Central Brain for Asta Real Estate Intelligence.",
    version="3.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---

class PropertyUnified(BaseModel):
    id: str
    title: str
    price: float
    location: str
    roi_score: float
    sentiment_score: float
    investment_vibe: str
    latitude: float
    longitude: float
    last_seen_at: str
    whatsapp_link: Optional[str]
    # "Trust Bullets" - Context aware (Rent vs Buy)
    why_it_scored: List[str] = Field(..., description="List of reasons justifying the score.")

class SuggestionChip(BaseModel):
    label: str
    emoji: str
    query_text: str
    category: str

class SearchSuggestions(BaseModel):
    headline: str
    chips: List[SuggestionChip]

class NearbyQuery(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 2.0
    # Optional: If the frontend knows the name (e.g. from Google Places), pass it for better messaging
    location_name: Optional[str] = None 

# --- HELPER FUNCTIONS ---

def clean_json_text(text):
    if not text: return ""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()

def determine_listing_type(item: Dict) -> str:
    """Heuristic to guess if Rent or Sale if not explicit in DB."""
    title = item.get('title', '').lower()
    price = item.get('price', 0)
    
    # Simple Heuristics for MVP
    if 'rent' in title or 'lease' in title or 'month' in title:
        return 'RENT'
    # In Ghana, prices < 20,000 usually imply rent (unless it's land/uncompleted)
    if price < 20000: 
        return 'RENT'
    return 'SALE'

def generate_trust_bullets(item: Dict) -> List[str]:
    """
    Generates Context-Aware 'Why' bullets.
    Differentiates between Renter needs and Buyer needs.
    """
    reasons = []
    listing_type = determine_listing_type(item)
    
    # 1. Location Logic (Universal)
    loc = item.get('location', '').lower()
    is_prime = any(x in loc for x in ['airport', 'cantonments', 'east legon', 'labone'])
    is_emerging = any(x in loc for x in ['oyarifa', 'pok uase', 'prampram', 'aburi'])

    # 2. Context Logic: BUY vs RENT
    if listing_type == 'SALE':
        # Buyer/Investor Focus: ROI, Growth, Yield
        score = item.get('roi_score', 0)
        if score >= 9.0: reasons.append("💎 Rare High-Yield Asset")
        elif score >= 8.0: reasons.append("📈 Strong Capital Appreciation")
        
        if is_prime: reasons.append("📍 Blue-Chip Location")
        if is_emerging: reasons.append("🚀 High Growth Corridor")
        
    else: # RENT
        # Renter Focus: Price, Lifestyle, Safety
        if is_prime: reasons.append("🌟 Premium Lifestyle Area")
        if is_emerging: reasons.append("💰 Competitive Rental Price")
        
        # Heuristic for "Fair Price" (MVP: if score is high, assume price is good)
        if item.get('roi_score', 0) > 7.5:
            reasons.append("⚖️ Fair Market Rent")

    # 3. Social Logic (Generalized - Competitive Edge)
    # Never say "TikTok". Say "Digital Engagement".
    sentiment = item.get('sentiment_score', 0)
    if sentiment > 0.6: 
        reasons.append("🔥 High Market Interest") # Vague but exciting
    elif sentiment > 0.3:
        reasons.append("👀 Frequently Viewed")

    # Fallback
    if not reasons:
        reasons.append("✅ Verified Listing")
        
    return reasons

# --- ENDPOINTS ---

@app.get("/properties/unified", response_model=List[PropertyUnified], tags=["Core Data"])
def get_unified_properties(limit: int = 50):
    response = supabase.table("v_property_details").select("*").limit(limit).execute()
    data = response.data
    
    for item in data:
        # WhatsApp Logic
        agent_phone = item.get('agent_phone', '233500000000') 
        clean_phone = re.sub(r"[^0-9]", "", str(agent_phone))
        ref_id = item.get('id', 'Unknown')[-6:]
        title = item.get('title', 'Property')
        msg = quote(f"Hello, I am interested in '{title}' seen on Asta Insights [Ref: {ref_id}]. Is it available?")
        item['whatsapp_link'] = f"https://wa.me/{clean_phone}?text={msg}"
        
        # CONTEXT-AWARE TRUST BULLETS
        item['why_it_scored'] = generate_trust_bullets(item)

    return data

@app.post("/properties/nearby", tags=["Maps"])
def find_nearby_properties(query: NearbyQuery):
    """
    **Human-Like Radius Search.**
    Returns a friendly message if the search had to be expanded.
    """
    user_lat = query.latitude
    user_lon = query.longitude
    current_radius = query.radius_km
    
    expansion_tiers = [current_radius, 5.0, 15.0, 50.0]
    expansion_tiers = [r for r in expansion_tiers if r >= current_radius]
    if not expansion_tiers: expansion_tiers = [current_radius]

    final_results = []
    used_radius = current_radius

    for radius in expansion_tiers:
        radius_meters = radius * 1000
        try:
            response = supabase.rpc("search_nearby_properties", {
                "user_lat": user_lat, 
                "user_lon": user_lon, 
                "radius_meters": radius_meters
            }).execute()
            
            if response.data and len(response.data) > 0:
                final_results = response.data
                used_radius = radius
                break 
        except Exception:
            continue

    # HUMAN MESSAGING LOGIC
    friendly_msg = f"Found {len(final_results)} homes within {used_radius}km."
    
    # Did we have to expand?
    if used_radius > query.radius_km:
        loc_name = query.location_name if query.location_name else "your exact location"
        
        # Dynamic Human Response
        friendly_msg = (
            f"We couldn't find the exact property in {loc_name}, "
            f"but we found similar listings {int(used_radius)}km away."
        )
    elif len(final_results) == 0:
         friendly_msg = "We couldn't find any listings in this area just yet."

    return {
        "center": {"lat": user_lat, "lon": user_lon},
        "radius_km_requested": query.radius_km,
        "radius_km_actual": used_radius,
        "expanded_search": used_radius > query.radius_km,
        "human_message": friendly_msg, # <--- Frontend displays this directly
        "count": len(final_results),
        "results": final_results
    }

@app.get("/search/suggestions", response_model=SearchSuggestions, tags=["AI Features"])
def get_search_suggestions():
    return {
        "headline": "What are you looking for?",
        "chips": [
            {
                "label": "High Yield", 
                "emoji": "💰", 
                "query_text": "Show me high ROI investment properties in Accra",
                "category": "Investment"
            },
            {
                "label": "Secure Living", 
                "emoji": "🛡️", 
                "query_text": "Gated communities with security in East Legon or Cantonments",
                "category": "Lifestyle"
            },
            {
                "label": "Affordable Rentals", 
                "emoji": "🔑", 
                "query_text": "1 or 2 bedroom apartments for rent under 3000 cedis",
                "category": "Rent"
            },
            {
                "label": "Short Stay", 
                "emoji": "🧳", 
                "query_text": "Apartments suitable for Airbnb near the Airport",
                "category": "Investment"
            }
        ]
    }

# --- EXISTING ENDPOINTS (Search, GeoJSON, GPS, Social) ---

class SearchQuery(BaseModel):
    query: str

class SearchResponse(BaseModel):
    interpreted_filters: Dict[str, Any]
    results: List[Dict[str, Any]]
    match_count: int

class GPSResult(BaseModel):
    found: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    message: str

class SocialSignal(BaseModel):
    platform: str
    content: str
    detected_location: Optional[str]
    summary: str
    created_at: str

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class GeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

@app.get("/properties/geojson", response_model=GeoJSONCollection, tags=["Maps"])
def get_property_heatmap():
    response = supabase.table("v_property_details").select("*").limit(500).execute()
    features = []
    for item in response.data:
        feat = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [item['longitude'], item['latitude']]},
            "properties": {"id": item['id'], "price": item['price'], "roi_score": item['roi_score']}
        }
        features.append(feat)
    return {"type": "FeatureCollection", "features": features}

@app.post("/search/ai", response_model=SearchResponse, tags=["AI Features"])
def ai_semantic_search(search: SearchQuery):
    user_query = search.query
    prompt = f"""
    You are a SQL Filter Generator. Query: "{user_query}"
    Extract: location_keyword, min_price, max_price, keywords (list). JSON ONLY.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        filters = json.loads(clean_json_text(response.text))
        query = supabase.table("v_property_details").select("*")
        if filters.get('location_keyword'): query = query.ilike("location", f"%{filters['location_keyword']}%")
        if filters.get('max_price'): query = query.lte("price", filters['max_price'])
        if filters.get('min_price'): query = query.gte("price", filters['min_price'])
        results = query.limit(20).execute()
        return {"interpreted_filters": filters, "results": results.data, "match_count": len(results.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/utils/extract-gps", response_model=GPSResult, tags=["Utilities"])
async def extract_gps(
    file: UploadFile = File(...), 
    text_hint: Optional[str] = Form(None) # <--- UPDATED: Accepts "GA-123-4567" from form
):
    """
    **The 'Lazy Agent' Locator.**
    
    Accepts an Image AND an optional Text Hint.
    1. Checks Image EXIF.
    2. Checks Text Hint for 'GA-XX-XXX' (Ghana Post) or Plus Codes.
    3. Checks Image Visuals (AI Vision).
    """
    try:
        # Pass the hint to the orchestrator in utils
        lat, lon, msg = await extract_gps_from_file(file, text_hint)
        
        if lat is not None and lon is not None:
            return {
                "found": True, 
                "latitude": lat, 
                "longitude": lon, 
                "message": msg
            }
        else:
            return {"found": False, "message": msg}
    except Exception as e:
        return {"found": False, "message": f"Error processing: {str(e)}"}

@app.get("/signals/latest", response_model=List[SocialSignal], tags=["Social Intel"])
def get_social_signals(limit: int = 10):
    response = supabase.table("social_signals").select("*").order("created_at", desc=True).limit(limit).execute()
    return response.data

# --- LAZY LISTING UTILS ---

async def upload_image_to_supabase(file: UploadFile, path: str) -> str:
    """Uploads a file to Supabase Storage and returns the Public URL."""
    file_bytes = await file.read()
    bucket_name = "properties" # Ensure this bucket exists in Supabase
    
    # Upload
    supabase.storage.from_(bucket_name).upload(
        path,
        file_bytes,
        {"content-type": file.content_type}
    )
    
    # Get Public URL
    public_url = supabase.storage.from_(bucket_name).get_public_url(path)
    return public_url

# --- LAZY LISTING ENDPOINT ---

@app.post("/listings/create", tags=["Lazy Agent"])
async def create_lazy_listing(
    price: float = Form(...),
    currency: str = Form("GHS"),
    description: Optional[str] = Form(None),
    location_hint: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """
    **The 'Lazy Agent' Publisher.**
    1. Extracts GPS from the first image or text hint.
    2. Auto-detects Neighborhood name (Reverse Geocoding).
    3. Uploads all images to Supabase.
    4. Creates the property record.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No images provided.")

    # 1. LOCATION INTELLIGENCE 📍
    # We use the first image + hint to resolve location
    lat, lon, loc_msg = await extract_gps_from_file(files[0], location_hint)
    
    # Reset file cursor after reading for GPS
    await files[0].seek(0)
    
    if not lat or not lon:
        # Fallback: If we can't find location, default to Accra Center (or handle error)
        # For MVP, we accept it but mark it 'Unverified'
        lat, lon = 5.6037, -0.1870 # Default Osu
        location_name = "Unverified Location"
    else:
        # Auto-Name the location (e.g. "East Legon")
        from api.utils import reverse_geocode
        location_name = reverse_geocode(lat, lon)

    # 2. IMAGE UPLOAD PARALLELIZATION 📸
    image_urls = []
    import uuid
    import time
    
    # Generate a unique batch ID for this property
    property_id = str(uuid.uuid4())
    
    for idx, file in enumerate(files):
        # Create unique filename: prop_id/img_0.jpg
        ext = file.filename.split('.')[-1]
        file_path = f"{property_id}/img_{idx}.{ext}"
        
        try:
            url = await upload_image_to_supabase(file, file_path)
            image_urls.append(url)
        except Exception as e:
            print(f"Upload failed for {file.filename}: {e}")

    # 3. SMART TITLE GENERATION 🧠
    # If no description, auto-generate title
    title = f"{len(files)} Bedroom Property in {location_name}" # Placeholder logic
    if description:
        title = description[:50] + "..."

    # 4. DATABASE INSERTION 💾
    new_property = {
        "id": property_id,
        "title": title,
        "description": description or "Uploaded via Lazy Agent",
        "price": price,
        "currency": currency,
        "location": location_name,
        "latitude": lat,
        "longitude": lon,
        "image_urls": image_urls, # Ensure your DB has this column (array or jsonb)
        "created_at": "now()",
        "agent_id": "anon_agent" # Replace with auth user ID later
    }
    
    try:
        # Insert into 'properties' table
        data = supabase.table("properties").insert(new_property).execute()
        return {
            "status": "success",
            "message": "Property listed successfully!",
            "location_detected": location_name,
            "coordinates": {"lat": lat, "lon": lon},
            "property_id": property_id,
            "images_count": len(image_urls)
        }
    except Exception as e:
        print(f"DB Error: {e}")
        # Even if DB fails, return what we have for debugging
        return {
            "status": "partial_success", 
            "error": str(e),
            "derived_data": new_property
        }
