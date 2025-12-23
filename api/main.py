from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import uuid
import io
import json
from PIL import Image
from api.utils import extract_gps_from_file, reverse_geocode, generate_property_insights, supabase, client, types

app = FastAPI(
    title="Asta Insights API",
    description="AI-Powered Real Estate Intelligence for Ghana",
    version="3.9"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SCHEMAS ---
class ChatRequest(BaseModel):
    query: str

# --- IMAGE COMPRESSION UTILS (DATA SAVER) 📉 ---

def compress_image(file_bytes: bytes) -> bytes:
    """
    Resizes image to max 1080p width and compresses to JPEG Quality 70.
    Standardizes uploads for the Ghanaian mobile network context.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        
        # Convert to RGB (fixes RGBA/P issues)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Resize if width > 1080
        base_width = 1080
        if img.size[0] > base_width:
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            
        # Compress
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=70, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Compression failed: {e}")
        return file_bytes # Fallback to original if compression fails

async def upload_image_to_supabase(file_bytes: bytes, path: str, content_type: str = "image/jpeg") -> str:
    bucket_name = "properties"
    try:
        supabase.storage.from_(bucket_name).upload(path, file_bytes, {"content-type": content_type})
        return supabase.storage.from_(bucket_name).get_public_url(path)
    except Exception as e:
        print(f"Supabase Upload Error: {e}")
        return ""

# --- ENDPOINTS ---

@app.get("/", tags=["Health"])
def read_root():
    return {"status": "active", "system": "Asta Insights API v3.9 (GeoJSON + Unified Enabled)", "docs_url": "/docs"}

# --- 1. CORE UTILITIES ---

@app.post("/utils/extract-gps", tags=["Utilities"])
async def extract_gps(
    file: UploadFile = File(...),
    text_hint: Optional[str] = Form(None)
):
    lat, lon, msg = await extract_gps_from_file(file, text_hint)
    return {
        "found": lat is not None,
        "latitude": lat,
        "longitude": lon,
        "message": msg
    }

# --- 2. THE LAZY AGENT (UPLOAD) ---

@app.post("/listings/create", tags=["Lazy Agent"])
async def create_lazy_listing(
    price: float = Form(...),
    listing_type: str = Form("SALE"), # Default to SALE
    currency: str = Form("GHS"),
    description: Optional[str] = Form(None),
    location_hint: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """
    **The Lazy Publisher.**
    Extracts GPS, Compresses Images, Generates AI Insights, and Saves to DB.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No images provided.")

    clean_type = listing_type.upper().strip()
    if clean_type not in ["SALE", "RENT"]: clean_type = "SALE"

    # 1. First Image Logic (GPS & AI)
    first_image_bytes = await files[0].read()
    await files[0].seek(0)
    lat, lon, loc_msg = await extract_gps_from_file(files[0], location_hint)
    
    if not lat or not lon:
        lat, lon = 5.6037, -0.1870 # Accra Center Default
        location_name = "Unverified Location"
    else:
        location_name = reverse_geocode(lat, lon)

    # 2. AI Insights
    insights = generate_property_insights(first_image_bytes, price, location_name, clean_type)
    
    # 3. Upload & Compress Loop
    image_urls = []
    property_id = str(uuid.uuid4())
    
    for idx, file in enumerate(files):
        await file.seek(0)
        raw_bytes = await file.read()
        compressed_bytes = compress_image(raw_bytes)
        file_path = f"{property_id}/img_{idx}.jpg"
        url = await upload_image_to_supabase(compressed_bytes, file_path)
        if url: image_urls.append(url)

    # 4. Save to DB
    auto_title = f"{insights.get('vibe', 'New')} Property for {clean_type.title()} in {location_name}"
    
    new_property = {
        "id": property_id,
        "title": description[:50] + "..." if description else auto_title,
        "description": description or f"AI Summary: {insights.get('vibe')}. {'; '.join(insights.get('trust_bullets', []))}",
        "price": price,
        "currency": currency,
        "listing_type": clean_type,
        "location": location_name,
        "latitude": lat,
        "longitude": lon,
        "image_urls": image_urls,
        "agent_id": "anon_agent",
        "created_at": "now()",
        "roi_score": insights.get("score", 0),
        "trust_bullets": insights.get("trust_bullets", []),
        "vibe": insights.get("vibe", "Standard")
    }
    
    try:
        supabase.table("properties").insert(new_property).execute()
        return {
            "status": "success",
            "location": location_name,
            "coordinates": {"lat": lat, "lon": lon},
            "insights": insights
        }
    except Exception as e:
        print(f"Insert Error: {e}")
        return {"status": "partial_success", "error": str(e)}

# --- 3. DATA VISUALIZATION ENDPOINTS (RESTORED) --- 🆕

@app.get("/properties/unified", tags=["Dashboard"])
def get_unified_properties():
    """
    **Unified Table Endpoint.**
    Returns clean, normalized data for the Dashboard Grid View.
    """
    try:
        response = supabase.table("properties").select("*").order("created_at", desc=True).limit(100).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/properties/geojson", tags=["Maps"])
def get_properties_geojson():
    """
    **Mapbox Source Endpoint.**
    Returns properties as a GeoJSON FeatureCollection for easy map plotting.
    """
    try:
        # Fetch properties with valid coordinates
        response = supabase.table("properties").select("id, title, price, currency, latitude, longitude, roi_score, vibe").neq("latitude", None).execute()
        properties = response.data
        
        features = []
        for prop in properties:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(prop["longitude"]), float(prop["latitude"])]
                },
                "properties": {
                    "id": prop["id"],
                    "title": prop["title"],
                    "price": prop["price"],
                    "currency": prop["currency"],
                    "roi_score": prop["roi_score"],
                    "vibe": prop["vibe"]
                }
            })
            
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        # Return empty valid GeoJSON on error to prevent map crash
        return {"type": "FeatureCollection", "features": []}

# --- 4. USER EXPERIENCE ---

@app.get("/listings/search", tags=["User Experience"])
def smart_radius_search(lat: float, lon: float, radius_km: int = 5):
    """**Smart Auto-Expanding Search.**"""
    current_radius = radius_km
    max_radius = 50 
    results = []
    
    while len(results) == 0 and current_radius <= max_radius:
        try:
            response = supabase.rpc("nearby_properties", {
                "lat": lat, "long": lon, "radius_km": current_radius
            }).execute()
            results = response.data
            if len(results) == 0: current_radius += 10
        except: break
            
    return {
        "results": results or [],
        "radius_used": current_radius,
        "expanded": current_radius > radius_km,
        "message": f"Found {len(results) if results else 0} properties within {current_radius}km"
    }

@app.get("/listings/tags", tags=["User Experience"])
def get_trending_tags():
    """**Trending Chips.**"""
    try:
        response = supabase.table("properties").select("vibe, location").execute()
        data = response.data
        locations = {}
        vibes = {}
        for item in data:
            loc = item.get('location', 'Accra').split(',')[0].strip()
            vibe = item.get('vibe', 'Standard')
            if loc: locations[loc] = locations.get(loc, 0) + 1
            if vibe: vibes[vibe] = vibes.get(vibe, 0) + 1
            
        top_locs = sorted(locations, key=locations.get, reverse=True)[:5]
        top_vibes = sorted(vibes, key=vibes.get, reverse=True)[:5]
        
        return {
            "locations": top_locs, 
            "vibes": top_vibes, 
            "chips": [f"📍 {l}" for l in top_locs] + [f"✨ {v}" for v in top_vibes]
        }
    except:
        return {"chips": ["📍 East Legon", "✨ Luxury"]}

# --- 5. DEMO & AI ---

@app.post("/agent/chat", tags=["Demo"])
def chat_with_data(request: ChatRequest):
    """**The Oracle Demo.**"""
    try:
        response = supabase.table("properties").select("title, price, listing_type, roi_score, vibe").order("created_at", desc=True).limit(10).execute()
        market_data = response.data
        
        prompt = f"""
        You are Asta, an AI Real Estate Analyst for Ghana.
        Live Data (Last 10 Listings): {json.dumps(market_data)}
        User Question: "{request.query}"
        Answer based ONLY on the data provided. Be professional.
        """
        model_response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return {"reply": model_response.text}
    except Exception as e:
        return {"reply": f"System Error: {str(e)}"}
