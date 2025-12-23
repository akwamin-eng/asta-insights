from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
import os
import uuid
import io
from PIL import Image
from api.utils import extract_gps_from_file, reverse_geocode, generate_property_insights, supabase

app = FastAPI(
    title="Asta Insights API",
    description="AI-Powered Real Estate Intelligence for Ghana",
    version="3.6"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "active", "system": "Asta Insights API v3.6 (Rent/Sale Support)", "docs_url": "/docs"}

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

@app.post("/listings/create", tags=["Lazy Agent"])
async def create_lazy_listing(
    price: float = Form(...),
    listing_type: str = Form("SALE"), # Default to SALE if missing
    currency: str = Form("GHS"),
    description: Optional[str] = Form(None),
    location_hint: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """
    **The Lazy Publisher.**
    1. Extracts GPS (Omni-Parser).
    2. Auto-Names Location.
    3. Compresses Images (Data Saver).
    4. **Generates Context-Aware Insights (Rent vs Sale).**
    5. Saves to DB.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No images provided.")

    # Validate Listing Type
    clean_type = listing_type.upper().strip()
    if clean_type not in ["SALE", "RENT"]:
        clean_type = "SALE"

    # 1. READ FIRST IMAGE FOR GPS & AI
    first_image_bytes = await files[0].read()
    
    # 2. GPS & NAMING
    # Reset cursor first since we read bytes above
    await files[0].seek(0)
    lat, lon, loc_msg = await extract_gps_from_file(files[0], location_hint)
    
    if not lat or not lon:
        lat, lon = 5.6037, -0.1870 # Default to Accra Center
        location_name = "Unverified Location"
    else:
        location_name = reverse_geocode(lat, lon)

    # 3. AI TRUST ANALYSIS (Context Aware) 🧠
    # Use the raw bytes of first image for analysis
    insights = generate_property_insights(first_image_bytes, price, location_name, clean_type)
    
    # 4. COMPRESSION & UPLOAD LOOP 📸
    image_urls = []
    property_id = str(uuid.uuid4())
    
    for idx, file in enumerate(files):
        await file.seek(0)
        raw_bytes = await file.read()
        
        # COMPRESS
        compressed_bytes = compress_image(raw_bytes)
        
        # UPLOAD
        file_path = f"{property_id}/img_{idx}.jpg"
        url = await upload_image_to_supabase(compressed_bytes, file_path)
        if url: image_urls.append(url)

    # 5. DB INSERT
    # Logic: Auto-generate title based on Rent/Sale context
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
            "type": clean_type,
            "coordinates": {"lat": lat, "lon": lon},
            "insights": insights,
            "images_uploaded": len(image_urls)
        }
    except Exception as e:
        print(f"Insert Error: {e}")
        return {"status": "partial_success", "error": str(e), "data": new_property}

@app.get("/listings/search", tags=["User Experience"])
def smart_radius_search(
    lat: float, 
    lon: float, 
    radius_km: int = 5
):
    """
    **Smart Auto-Expanding Search.**
    Prevents 'Empty Map Syndrome' by expanding radius if 0 results found.
    Requires Supabase RPC function 'nearby_properties'.
    """
    current_radius = radius_km
    max_radius = 50 
    results = []
    
    # Loop to expand radius
    while len(results) == 0 and current_radius <= max_radius:
        try:
            # Call PostGIS RPC
            response = supabase.rpc("nearby_properties", {
                "lat": lat, 
                "long": lon, 
                "radius_km": current_radius
            }).execute()
            results = response.data
            
            if len(results) == 0:
                current_radius += 10 # Step up
        except Exception as e:
            # If RPC missing, just break loop and return empty
            break
            
    return {
        "results": results or [],
        "radius_used": current_radius,
        "expanded": current_radius > radius_km,
        "message": f"Found {len(results) if results else 0} properties within {current_radius}km"
    }
