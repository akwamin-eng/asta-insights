import os
import re
import json
import requests
from typing import Tuple, Optional, Any
from io import BytesIO
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from google import genai
from google.genai import types
from dotenv import load_dotenv
import openlocationcode as olc 
import pillow_heif 
from supabase import create_client

# Load env
load_dotenv()

pillow_heif.register_heif_opener()

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# --- REGEX PATTERNS ---
# 1. Ghana Post (e.g., GA-183-8192 or GA1838192)
GHANA_POST_REGEX = r"([A-Z]{2}-?\d{3,4}-?\d{3,4})"
# 2. Plus Code (e.g., 8FQM+57)
PLUS_CODE_REGEX = r"([23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]{2,3})"
# 3. Raw Coordinates (e.g., 5.603, -0.187 or 5.603,-0.187)
LAT_LON_REGEX = r"(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)"
# 4. Google Maps Link
GOOGLE_LINK_REGEX = r"maps\.app\.goo\.gl\/[a-zA-Z0-9]+"

def _convert_to_degrees(value):
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except:
        return 0.0

def get_exif_gps(image_bytes: bytes) -> Tuple[Optional[float], Optional[float]]:
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
        if gps_info.get('GPSLatitudeRef') == 'S': lat = -lat
        if gps_info.get('GPSLongitudeRef') == 'W': lon = -lon
        return lat, lon
    except Exception:
        return None, None

def normalize_ghana_post(address: str) -> str:
    clean = address.replace("-", "").replace(" ", "").upper()
    if len(clean) >= 9: 
        return f"{clean[:2]}-{clean[2:5]}-{clean[5:]}"
    return address

def recursive_find_coords(data: Any) -> Tuple[Optional[float], Optional[float]]:
    if isinstance(data, dict):
        keys = {k.lower(): v for k, v in data.items()}
        lat = keys.get('centerlatitude') or keys.get('nlat') or keys.get('latitude') or keys.get('lat')
        lon = keys.get('centerlongitude') or keys.get('wlong') or keys.get('longitude') or keys.get('lng') or keys.get('long')
        if lat is not None and lon is not None:
            try: return float(lat), float(lon)
            except: pass
        for value in data.values():
            found_lat, found_lon = recursive_find_coords(value)
            if found_lat and found_lon: return found_lat, found_lon
    elif isinstance(data, list):
        for item in data:
            found_lat, found_lon = recursive_find_coords(item)
            if found_lat and found_lon: return found_lat, found_lon
    return None, None

def cache_address(address: str, lat: float, lon: float, source: str):
    try:
        supabase.table("location_cache").upsert({
            "address_id": address,
            "latitude": lat,
            "longitude": lon,
            "source": source
        }).execute()
        print(f"✅ Cached {address}")
    except Exception as e:
        print(f"Cache Write Failed: {e}")

def check_cache(address: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        resp = supabase.table("location_cache").select("*").eq("address_id", address).execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0]['latitude'], resp.data[0]['longitude']
    except Exception:
        pass
    return None, None

def query_ghana_post_direct(address: str) -> Tuple[Optional[float], Optional[float], str]:
    formatted_address = normalize_ghana_post(address)
    c_lat, c_lon = check_cache(formatted_address)
    if c_lat and c_lon:
        return c_lat, c_lon, f"Verified via Asta Cache: {formatted_address}"

    url = "https://ghanapostgps.sperixlabs.org/get-location"
    headers = {'User-Agent': 'Mozilla/5.0 (Compatible; AstaInsights/1.0)', 'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        resp = requests.post(url, data={'address': formatted_address}, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('found'):
                lat, lon = recursive_find_coords(data)
                if lat and lon:
                    cache_address(formatted_address, lat, lon, 'bridge')
                    return lat, lon, "Verified via GhanaPostGPS"
                return None, None, "Address found but coordinates missing."
            else:
                return None, None, "Address not found in GhanaPost Database"
        return None, None, f"Bridge Error: {resp.status_code}"
    except Exception as e:
        return None, None, f"GhanaPost Connection Failed: {str(e)}"

def geocode_with_google(address_text: str) -> Tuple[Optional[float], Optional[float]]:
    if not GOOGLE_API_KEY: return None, None
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": f"{address_text}, Ghana", "key": GOOGLE_API_KEY}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data['status'] == 'OK' and len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            if data['results'][0].get('geometry', {}).get('location_type') == 'ROOFTOP':
                 cache_address(normalize_ghana_post(address_text), location['lat'], location['lng'], 'google')
            return location['lat'], location['lng']
    except Exception:
        pass
    return None, None

def resolve_text_location(text_input: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    The Omni-Parser: Handles GhanaPost, Plus Codes, and Raw Lat/Lon.
    """
    if not text_input: return None, None, ""

    # 1. Check for Raw Lat, Lon (e.g. 5.603, -0.187)
    coord_match = re.search(LAT_LON_REGEX, text_input)
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            # Basic validation for Ghana (approx limits)
            if 4.0 <= lat <= 12.0 and -4.0 <= lon <= 2.0:
                 return lat, lon, "Detected Raw Coordinates"
            return lat, lon, "Detected Coordinates (Outside Ghana Warning)"
        except ValueError:
            pass

    # 2. Check Ghana Post GPS
    gp_match = re.search(GHANA_POST_REGEX, text_input.upper())
    if gp_match:
        raw_address = gp_match.group(0)
        lat, lon, status_msg = query_ghana_post_direct(raw_address)
        if lat and lon: return lat, lon, f"{status_msg}: {raw_address}"
        lat, lon = geocode_with_google(raw_address)
        if lat and lon: return lat, lon, f"Resolved via Google Maps: {raw_address}"
        return None, None, f"Parsing Failed: {status_msg}"

    # 3. Check Plus Codes
    pc_match = re.search(PLUS_CODE_REGEX, text_input.upper())
    if pc_match:
        code = pc_match.group(0)
        try:
            if olc.isValid(code):
                decoded = olc.decode(code)
                return decoded.latitudeCenter, decoded.longitudeCenter, f"Decoded Plus Code: {code}"
        except: pass
    return None, None, ""

async def extract_gps_from_file(file_obj, text_hint: str = None) -> Tuple[Optional[float], Optional[float], str]:
    file_bytes = await file_obj.read()
    lat, lon = get_exif_gps(file_bytes)
    if lat and lon: return lat, lon, "High Precision (EXIF)"
    err_msg = ""
    if text_hint:
        lat, lon, msg = resolve_text_location(text_hint)
        if lat and lon: return lat, lon, msg
        err_msg = msg
    try:
        if len(file_bytes) > 0:
            # Re-adding AI Logic
            prompt = "Analyze this image. Look for 'Ghana Post GPS' addresses painted on walls. Return JSON {found, latitude, longitude, reason}"
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[types.Part.from_bytes(data=file_bytes, mime_type="image/jpeg"), prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(re.sub(r"```json|```", "", response.text).strip())
            if data.get("found"):
                return data.get("latitude"), data.get("longitude"), f"AI Vision: {data.get('reason')}"
    except: pass
    final_msg = f"Location Failed. {err_msg}" if err_msg else "Location detection failed."
    return None, None, final_msg
