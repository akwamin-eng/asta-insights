import os
import re
import json
from typing import Tuple, Optional
from io import BytesIO
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from google import genai
from google.genai import types
from dotenv import load_dotenv
import openlocationcode as olc # Google Plus Codes

# Load env
load_dotenv()

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# --- GHANA DIGITAL ADDRESS CONSTANTS (Simplified Mapping) ---
# In a real prod app, you would query the GhanaPostGPS API. 
# For MVP, we use Gemini to resolve the address to Lat/Lon if Regex matches.
GHANA_POST_REGEX = r"([A-Z]{2}-\d{3,4}-\d{3,4})"
PLUS_CODE_REGEX = r"([23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]{2,3})"
GOOGLE_LINK_REGEX = r"maps\.app\.goo\.gl\/[a-zA-Z0-9]+"

def _convert_to_degrees(value):
    """Helper for EXIF conversion."""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_exif_gps(image_bytes: bytes) -> Tuple[Optional[float], Optional[float]]:
    """TIER 1: EXIF Extraction."""
    try:
        image = Image.open(BytesIO(image_bytes))
        exif_data = image._getexif()
        if not exif_data: return None, None

        gps_info = {}
        for tag, value in exif_data.items():
            if TAGS.get(tag) == "GPSInfo":
                for t in value:
                    gps_info[GPSTAGS.get(t, t)] = value[t]

        if not gps_info: return None, None

        lat = _convert_to_degrees(gps_info['GPSLatitude'])
        lon = _convert_to_degrees(gps_info['GPSLongitude'])

        if gps_info['GPSLatitudeRef'] != 'N': lat = -lat
        if gps_info['GPSLongitudeRef'] != 'E': lon = -lon

        return lat, lon
    except Exception:
        return None, None

def resolve_text_location(text_input: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    TIER 2 & 3: Text Parser (Ghana Post, Plus Code, Google Links).
    """
    if not text_input: return None, None, ""

    # A. Check Ghana Post GPS (e.g., GA-183-8192)
    gp_match = re.search(GHANA_POST_REGEX, text_input.upper())
    if gp_match:
        address = gp_match.group(0)
        # Ask Gemini to Geocode this specifically (since GhanaPost API is closed/paid)
        # Gemini often knows the major digital addresses or can approximate.
        return None, None, f"Detected Ghana Digital Address: {address}. (Requires Manual Verify or API)"

    # B. Check Plus Code (e.g., 8FQM+57 Accra)
    # We clean it to ensure it's a valid global code or local code
    pc_match = re.search(PLUS_CODE_REGEX, text_input.upper())
    if pc_match:
        code = pc_match.group(0)
        try:
            # If short code (e.g. 8FQM+57), we need a reference location (Accra). 
            # For MVP, assuming full code or handling via Gemini fallback.
            # But let's try strict decoding:
            if olc.isValid(code):
                decoded = olc.decode(code)
                return decoded.latitudeCenter, decoded.longitudeCenter, f"Decoded Plus Code: {code}"
        except:
            pass
            
    # C. Google Maps Link (Hard fallback)
    if re.search(GOOGLE_LINK_REGEX, text_input):
        return None, None, "Detected Google Maps Link (Frontend should expand this URL)"

    return None, None, ""

def get_ai_location_estimate(image_bytes: bytes) -> Tuple[Optional[float], Optional[float], str]:
    """TIER 4: Gemini Vision deduction."""
    print("🤖 Gemini Vision: analyzing image for landmarks...")
    prompt = """
    Analyze this real estate image for location clues.
    1. Look for 'Ghana Post GPS' addresses painted on walls (e.g. GA-123-4567).
    2. Look for landmarks.
    Return JSON: { "found": bool, "latitude": float, "longitude": float, "reason": str }
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(re.sub(r"```json|```", "", response.text).strip())
        if data.get("found"):
            return data.get("latitude"), data.get("longitude"), data.get("reason")
        return None, None, "No visual landmarks found."
    except Exception as e:
        return None, None, f"AI Error: {str(e)}"

async def extract_gps_from_file(file_obj, text_hint: str = None) -> Tuple[Optional[float], Optional[float], str]:
    """
    THE MASTER ORCHESTRATOR.
    1. Try EXIF.
    2. Try Text Hint (Ghana Post / Plus Code).
    3. Try AI Vision.
    """
    file_bytes = await file_obj.read()
    
    # 1. EXIF
    lat, lon = get_exif_gps(file_bytes)
    if lat and lon: return lat, lon, "High Precision (EXIF)"

    # 2. Text Hint (If agent typed something)
    if text_hint:
        lat, lon, msg = resolve_text_location(text_hint)
        if lat and lon: return lat, lon, msg
        if "Detected" in msg: return None, None, msg # Return the detection for manual handling

    # 3. AI Vision
    lat, lon, reason = get_ai_location_estimate(file_bytes)
    if lat and lon: return lat, lon, f"AI Vision: {reason}"

    return None, None, "Location detection failed."
