import os
import json
import re
from typing import Tuple, Optional
from io import BytesIO
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env to get Gemini Key inside the utility
load_dotenv()

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def _convert_to_degrees(value):
    """Helper to convert EXIF GPS format to decimal degrees."""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_exif_gps(image_bytes: bytes) -> Tuple[Optional[float], Optional[float]]:
    """
    TIER 1: Extract precise GPS from metadata.
    Returns (lat, lon) or (None, None).
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        exif_data = image._getexif()
        if not exif_data:
            return None, None

        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for t in value:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_info[sub_tag] = value[t]

        if not gps_info:
            return None, None

        lat = _convert_to_degrees(gps_info['GPSLatitude'])
        lon = _convert_to_degrees(gps_info['GPSLongitude'])

        if gps_info['GPSLatitudeRef'] != 'N': lat = -lat
        if gps_info['GPSLongitudeRef'] != 'E': lon = -lon

        return lat, lon
    except Exception:
        return None, None

def get_ai_location_estimate(image_bytes: bytes) -> Tuple[Optional[float], Optional[float], str]:
    """
    TIER 2 & 3: Use Gemini Vision to detect Landmarks & Text.
    Returns (lat, lon, reasoning_message).
    """
    print("🤖 Gemini Vision: analyzing image for landmarks...")
    prompt = """
    You are a Geo-Location Detective. Analyze this real estate image for location clues.
    
    1. LANDMARKS: Do you see famous buildings, distinct architecture, or well-known views?
    2. TEXT: Read ANY signs, billboards, shop names, or street signs (OCR).
    3. DEDUCTION: Combine these clues to estimate the location.
    
    If you can identify the location (e.g. 'Airport City Accra', 'Osu Oxford Street'), provide coordinates.
    If you cannot find any specific location clues, set found to false.
    
    Return JSON ONLY:
    {
        "found": boolean,
        "latitude": float or null,
        "longitude": float or null,
        "reason": "Saw 'Marina Mall' sign and distinct yellow arch."
    }
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        # Clean up JSON
        text = re.sub(r"```json\s*", "", response.text)
        text = re.sub(r"```\s*", "", text).strip()
        data = json.loads(text)
        
        if data.get("found"):
            return data.get("latitude"), data.get("longitude"), data.get("reason")
        
        return None, None, "AI analyzed image but found no recognizable landmarks or text."
        
    except Exception as e:
        print(f"AI Vision Error: {e}")
        return None, None, f"AI analysis failed: {str(e)}"

async def extract_gps_from_file(file_obj) -> Tuple[Optional[float], Optional[float], str]:
    """
    The Master Orchestrator:
    1. Tries EXIF (Fast, Precise).
    2. If fails, Tries AI Vision (Slower, Smart).
    """
    # 1. Read bytes once
    file_bytes = await file_obj.read()
    
    # 2. Try EXIF (Tier 1)
    lat, lon = get_exif_gps(file_bytes)
    if lat and lon:
        return lat, lon, "Extracted from EXIF Metadata (High Precision)"

    # 3. Try AI Vision (Tier 2 & 3)
    # Only fallback if EXIF failed or wasn't found
    print("⚠️ EXIF missing. Engaging Gemini Vision...")
    lat, lon, reason = get_ai_location_estimate(file_bytes)
    
    if lat and lon:
        return lat, lon, f"AI Estimation: {reason}"
        
    return None, None, "Location extraction failed (No EXIF, No recognizable landmarks)."
