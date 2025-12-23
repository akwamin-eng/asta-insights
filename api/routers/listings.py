from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import uuid
import json
from api.utils import (
    extract_gps_from_file, reverse_geocode, generate_property_insights, 
    supabase, compress_image, upload_image_to_supabase
)

router = APIRouter(tags=["Phase 1: Listings & Data"])

# --- 1. LAZY AGENT (CREATE) ---
@router.post("/listings/create")
async def create_lazy_listing(
    price: float = Form(...),
    listing_type: str = Form("SALE"),
    currency: str = Form("GHS"),
    description: Optional[str] = Form(None),
    location_hint: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    if not files: raise HTTPException(400, "No images provided.")
    clean_type = listing_type.upper().strip()
    if clean_type not in ["SALE", "RENT"]: clean_type = "SALE"

    first_bytes = await files[0].read()
    await files[0].seek(0)
    lat, lon, _ = await extract_gps_from_file(files[0], location_hint)
    
    if not lat: lat, lon = 5.6037, -0.1870
    location_name = reverse_geocode(lat, lon)
    insights = generate_property_insights(first_bytes, price, location_name, clean_type)

    image_urls = []
    prop_id = str(uuid.uuid4())
    for idx, file in enumerate(files):
        await file.seek(0)
        raw = await file.read()
        compressed = compress_image(raw)
        url = await upload_image_to_supabase(compressed, f"{prop_id}/img_{idx}.jpg")
        if url: image_urls.append(url)

    new_prop = {
        "id": prop_id,
        "title": description[:50] + "..." if description else f"{insights.get('vibe')} {clean_type.title()} in {location_name}",
        "description": description or f"AI Summary: {insights.get('vibe')}.",
        "price": price, "currency": currency, "listing_type": clean_type,
        "location": location_name, "latitude": lat, "longitude": lon,
        "image_urls": image_urls, "agent_id": "anon_agent", "created_at": "now()",
        "roi_score": insights.get("score", 0), "trust_bullets": insights.get("trust_bullets", []),
        "vibe": insights.get("vibe", "Standard")
    }
    
    try:
        supabase.table("properties").insert(new_prop).execute()
        return {"status": "success", "id": prop_id, "insights": insights}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# --- 2. UNIFIED TABLE (DASHBOARD) ---
@router.get("/properties/unified")
def get_unified_properties():
    try:
        response = supabase.table("properties").select("*").order("created_at", desc=True).limit(100).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. GEOJSON (MAP) ---
@router.get("/properties/geojson")
def get_properties_geojson():
    try:
        response = supabase.table("properties").select("id, title, price, currency, latitude, longitude, roi_score, vibe").neq("latitude", None).execute()
        features = []
        for prop in response.data:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(prop["longitude"]), float(prop["latitude"])]},
                "properties": prop
            })
        return {"type": "FeatureCollection", "features": features}
    except:
        return {"type": "FeatureCollection", "features": []}

# --- 4. SMART SEARCH ---
@router.get("/listings/search")
def smart_radius_search(lat: float, lon: float, radius_km: int = 5):
    curr_rad, max_rad, results = radius_km, 50, []
    while len(results) == 0 and curr_rad <= max_rad:
        try:
            res = supabase.rpc("nearby_properties", {"lat": lat, "long": lon, "radius_km": curr_rad}).execute()
            results = res.data
            if not results: curr_rad += 10
        except: break
    return {"results": results or [], "radius_used": curr_rad}

# --- 5. TRENDING TAGS ---
@router.get("/listings/tags")
def get_trending_tags():
    try:
        data = supabase.table("properties").select("vibe, location").execute().data
        locations, vibes = {}, {}
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
