import os
import json
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai import types

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
    description="""
    The Central Brain for Asta Real Estate Intelligence.
    
    ## Key Features:
    * **Unified Property Data**: Normalized listings with AI-enriched ROI scores.
    * **GeoJSON Heatmaps**: Optimized for Mapbox/Google Maps integration.
    * **Semantic Search**: "ChatGPT-style" search that translates natural language to SQL.
    * **GPS Extraction**: Auto-locates properties via EXIF image data.
    * **Spatial Search**: High-speed "Near Me" queries using PostGIS.
    * **Social Signals**: Real-time sentiment analysis from Reddit/TikTok.
    """,
    version="2.6.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS (Allow All for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC MODELS (The Documentation Layer) ---

class PropertyUnified(BaseModel):
    id: str = Field(..., description="Unique UUID of the property listing.")
    title: str = Field(..., description="The cleaned title of the listing.")
    price: float = Field(..., description="Price in GHS (Ghana Cedis).")
    location: str = Field(..., description="Normalized neighborhood name (e.g., 'East Legon').")
    roi_score: float = Field(..., description="AI-Calculated ROI Potential (0.0 - 10.0). 10 is best.")
    sentiment_score: float = Field(..., description="Market 'Vibe' Score (-1.0 to 1.0).")
    investment_vibe: str = Field(..., description="One-line AI verdict (e.g., 'Cash Flow King').")
    latitude: float = Field(..., description="Decimal Latitude for mapping.")
    longitude: float = Field(..., description="Decimal Longitude for mapping.")
    last_seen_at: str = Field(..., description="ISO 8601 Timestamp of last update.")

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any] = Field(..., description="Point geometry [lon, lat]")
    properties: Dict[str, Any] = Field(..., description="Minimal data for map interactions (id, price, roi).")

class GeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class SearchQuery(BaseModel):
    query: str = Field(..., example="3 bedroom house in Osu under 500k", description="Natural language search string.")

class SearchResponse(BaseModel):
    interpreted_filters: Dict[str, Any] = Field(..., description="How the AI understood your query.")
    results: List[Dict[str, Any]] = Field(..., description="Matching database rows.")
    match_count: int

class GPSResult(BaseModel):
    found: bool = Field(..., description="True if EXIF GPS data was successfully extracted.")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    message: str

class SocialSignal(BaseModel):
    platform: str = Field(..., example="reddit")
    content: str = Field(..., description="The raw post text.")
    detected_location: Optional[str] = Field(None, description="City/Area extracted by AI.")
    summary: str = Field(..., description="One-sentence AI summary of the complaint/insight.")
    created_at: str

class NearbyQuery(BaseModel):
    latitude: float = Field(..., example=5.6037, description="User's current latitude.")
    longitude: float = Field(..., example=-0.1870, description="User's current longitude.")
    radius_km: float = Field(2.0, example=5.0, description="Search radius in Kilometers.")

# --- HELPER FUNCTIONS ---
def clean_json_text(text):
    if not text: return ""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()

# --- ENDPOINTS ---

@app.get("/", tags=["System"])
def read_root():
    return {
        "status": "online", 
        "system": "Asta API v2.6", 
        "docs": "/docs", 
        "message": "Welcome. Visit /docs for interactive testing."
    }

@app.get("/properties/unified", response_model=List[PropertyUnified], tags=["Core Data"])
def get_unified_properties(limit: int = 50):
    """
    **Primary Endpoint for Lists & Tables.**
    
    Returns clean, normalized data backed by the `v_property_details` SQL View.
    Use this to populate the main dashboard grid.
    """
    response = supabase.table("v_property_details").select("*").limit(limit).execute()
    return response.data

@app.get("/properties/geojson", response_model=GeoJSONCollection, tags=["Maps"])
def get_property_heatmap():
    """
    **Optimized for Mapbox GL JS / Google Maps.**
    
    Returns a valid GeoJSON `FeatureCollection`.
    * **Frontend Usage:** Pass this URL directly to `map.addSource(..., { type: 'geojson', data: URL })`.
    * **Styling:** Use `properties.roi_score` to color-code markers (Red=Low, Green=High).
    """
    response = supabase.table("v_property_details").select("*").limit(500).execute()
    
    features = []
    for item in response.data:
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [item['longitude'], item['latitude']]
            },
            "properties": {
                "id": item['id'],
                "title": item['title'],
                "price": item['price'],
                "roi_score": item['roi_score'],
                "vibe": item['investment_vibe']
            }
        }
        features.append(feat)
    return {"type": "FeatureCollection", "features": features}

@app.post("/properties/nearby", tags=["Maps"])
def find_nearby_properties(query: NearbyQuery):
    """
    **Geo-Spatial Radius Search (PostGIS).**
    
    Uses high-speed spatial indexing to find properties within `radius_km` of the user.
    Returns results sorted by distance (closest first).
    """
    try:
        # Convert KM to Meters for PostGIS
        radius_meters = query.radius_km * 1000
        
        # Call the SQL Function (RPC)
        response = supabase.rpc("search_nearby_properties", {
            "user_lat": query.latitude, 
            "user_lon": query.longitude, 
            "radius_meters": radius_meters
        }).execute()
        
        return {
            "center": {"lat": query.latitude, "lon": query.longitude},
            "radius_meters": radius_meters,
            "count": len(response.data),
            "results": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spatial Query Failed: {str(e)}")

@app.post("/search/ai", response_model=SearchResponse, tags=["AI Features"])
def ai_semantic_search(search: SearchQuery):
    """
    **The 'ChatGPT' Search Bar.**
    
    1. Receives natural text (e.g. *"Safe 3 bedroom near airport"*).
    2. Asks Gemini to translate that intent into SQL filters.
    3. Executes the query and returns matches.
    """
    user_query = search.query
    print(f"🧠 AI Search processing: '{user_query}'")
    
    prompt = f"""
    You are a SQL Filter Generator for a Real Estate DB.
    User Query: "{user_query}"
    Extract search intent into JSON keys:
    - location_keyword: (e.g. 'Osu', 'Airport', 'Cantonments')
    - min_price: (number or null)
    - max_price: (number or null)
    - keywords: (list of strings like 'pool', 'security', 'shop')
    Return JSON ONLY.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        filters = json.loads(clean_json_text(response.text))
        
        query = supabase.table("v_property_details").select("*")
        
        # Apply Filters Dynamically
        if filters.get('location_keyword'):
            query = query.ilike("location", f"%{filters['location_keyword']}%")
        if filters.get('max_price'):
            query = query.lte("price", filters['max_price'])
        if filters.get('min_price'):
            query = query.gte("price", filters['min_price'])
            
        results = query.limit(20).execute()
        
        return {
            "interpreted_filters": filters,
            "results": results.data,
            "match_count": len(results.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Search failed: {str(e)}")

@app.post("/utils/extract-gps", response_model=GPSResult, tags=["Utilities"])
async def extract_gps(file: UploadFile = File(...)):
    """
    **For Agent Upload Forms.**
    
    Uploads a photo -> Returns `{ found: true, latitude: ..., longitude: ... }`.
    Use this to auto-fill the "Location" field when an agent uploads a property photo.
    """
    try:
        lat, lon = extract_gps_from_file(file.file)
        if lat is not None and lon is not None:
            return {
                "found": True, 
                "latitude": lat, 
                "longitude": lon, 
                "message": "GPS coordinates extracted successfully."
            }
        else:
            return {"found": False, "message": "No GPS metadata found in this image."}
    except Exception as e:
        return {"found": False, "message": f"Error processing image: {str(e)}"}

@app.get("/signals/latest", response_model=List[SocialSignal], tags=["Social Intel"])
def get_social_signals(limit: int = 10):
    """
    **Real-Time Street Sentiment.**
    
    Returns the latest Reddit/TikTok chatter flagged with location intelligence.
    Use this for the "Trending Alerts" ticker.
    """
    response = supabase.table("social_signals")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    return response.data
