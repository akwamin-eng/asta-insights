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
    * **World-Class GPS**: Extracts location from EXIF *or* uses AI Vision to recognize landmarks.
    * **Spatial Search**: High-speed "Near Me" queries using PostGIS.
    * **Social Signals**: Real-time sentiment analysis from Reddit/TikTok.
    """,
    version="2.7.0",
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

# --- PYDANTIC MODELS ---

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

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class GeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class SearchQuery(BaseModel):
    query: str = Field(..., example="3 bedroom house in Osu under 500k")

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

class NearbyQuery(BaseModel):
    latitude: float = Field(..., example=5.6037)
    longitude: float = Field(..., example=-0.1870)
    radius_km: float = Field(2.0, example=5.0)

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
        "system": "Asta API v2.7", 
        "docs": "/docs", 
        "message": "Welcome. Visit /docs for interactive testing."
    }

@app.get("/properties/unified", response_model=List[PropertyUnified], tags=["Core Data"])
def get_unified_properties(limit: int = 50):
    response = supabase.table("v_property_details").select("*").limit(limit).execute()
    return response.data

@app.get("/properties/geojson", response_model=GeoJSONCollection, tags=["Maps"])
def get_property_heatmap():
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
    try:
        radius_meters = query.radius_km * 1000
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
    **World-Class Locator (EXIF + AI Vision).**
    
    1. Checks for hidden GPS metadata (Precision: High).
    2. If missing, asks Gemini to look at the image (Landmarks/Signs) (Precision: Medium).
    """
    try:
        # AWAIT the new async function from utils
        lat, lon, msg = await extract_gps_from_file(file)
        
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
        return {"found": False, "message": f"Error processing image: {str(e)}"}

@app.get("/signals/latest", response_model=List[SocialSignal], tags=["Social Intel"])
def get_social_signals(limit: int = 10):
    response = supabase.table("social_signals")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    return response.data
