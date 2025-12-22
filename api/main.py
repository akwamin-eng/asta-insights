import os
import json
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

app = FastAPI(
    title="Asta Insights API",
    description="The Central Brain for Asta Real Estate Intelligence",
    version="2.1.0"
)

# Enable CORS (Allow All for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
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

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class GeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class SearchQuery(BaseModel):
    query: str

class GPSResult(BaseModel):
    found: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    message: str

# --- Helper Functions ---
def clean_json_text(text):
    if not text: return ""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "online", "system": "Asta API v2.1", "ready": True}

@app.post("/utils/extract-gps", response_model=GPSResult)
async def extract_gps(file: UploadFile = File(...)):
    """
    Receives an image file, extracts EXIF GPS data.
    Returns lat/lon if found, else returns found=False (triggering manual entry).
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
            return {
                "found": False, 
                "message": "No GPS metadata found in this image."
            }
    except Exception as e:
        return {"found": False, "message": f"Error processing image: {str(e)}"}

@app.get("/properties/unified", response_model=List[PropertyUnified])
def get_unified_properties(limit: int = 50):
    response = supabase.table("v_property_details").select("*").limit(limit).execute()
    return response.data

@app.get("/properties/geojson", response_model=GeoJSONCollection)
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

@app.post("/search/ai")
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
            
        results = query.limit(20).execute()
        return {
            "interpreted_filters": filters,
            "results": results.data,
            "match_count": len(results.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Search failed: {str(e)}")
