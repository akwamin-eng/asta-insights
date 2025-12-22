import os
import re
import json
import requests
from typing import Tuple, Optional
from io import BytesIO
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from google import genai
from google.genai import types
from dotenv import load_dotenv
import openlocationcode as olc 
import pillow_heif 

# Load env
load_dotenv()

pillow_heif.register_heif_opener()

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

GHANA_POST_REGEX = r"([A-Z]{2}-?\d{3,4}-?\d{3,4})"
PLUS_CODE_REGEX = r"([23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]{2,3})"
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

def get_coords_from_dict(data: dict) -> Tuple[Optional[float], Optional[float]]:
    """Helper to hunt for lat/lon keys case-insensitively"""
    # Normalize keys to lowercase
    keys = {k.lower(): v for k, v in data.items()}
    
    lat = keys.get('latitude') or keys.get('nlat') or keys.get('lat')
    lon = keys.get('longitude') or keys.get('wlong') or keys.get('long') or keys.get('lng')
    
    if lat and lon:
        return float(lat), float(lon)
    return None, None

def query_ghana_post_direct(address: str) -> Tuple[Optional[float], Optional[float], str]:
    formatted_address = normalize_ghana_post(address)
    url = "https://ghanapostgps.sperixlabs.org/get-location"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Compatible; AstaInsights/1.0)',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        resp = requests.post(url, data={'address': formatted_address}, headers=headers, timeout=8)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('found') and data.get('data'):
                # Try to parse the Table list
                if isinstance(data['data'], dict) and 'Table' in data['data']:
                     table_item = data['data']['Table'][0]
                     lat, lon = get_coords_from_dict(table_item)
                     if lat: return lat, lon, "Verified via GhanaPostGPS"
                
                # Sometimes it returns data directly not in a Table
                lat, lon = get_coords_from_dict(data['data'])
                if lat: return lat, lon, "Verified via GhanaPostGPS"
                
                return None, None, f"Address found but coordinates missing. Keys: {list(data.get('data', {}).keys())}"
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
            return location['lat'], location['lng']
    except Exception:
        pass
    return None, None

def resolve_text_location(text_input: str) -> Tuple[Optional[float], Optional[float], str]:
    if not text_input: return None, None, ""

    # A. Ghana Post GPS
    gp_match = re.search(GHANA_POST_REGEX, text_input.upper())
    if gp_match:
        raw_address = gp_match.group(0)
        
        # 1. Try Bridge
        lat, lon, status_msg = query_ghana_post_direct(raw_address)
        if lat and lon: return lat, lon, f"{status_msg}: {raw_address}"
        
        # 2. Fallback to Google
        lat, lon = geocode_with_google(raw_address)
        if lat and lon: return lat, lon, f"Resolved via Google Maps: {raw_address}"
            
        return None, None, f"Parsing Failed: {status_msg}"

    # B. Plus Codes
    pc_match = re.search(PLUS_CODE_REGEX, text_input.upper())
    if pc_match:
        code = pc_match.group(0)
        try:
            if olc.isValid(code):
                decoded = olc.decode(code)
                return decoded.latitudeCenter, decoded.longitudeCenter, f"Decoded Plus Code: {code}"
        except:
            pass

    return None, None, ""

async def extract_gps_from_file(file_obj, text_hint: str = None) -> Tuple[Optional[float], Optional[float], str]:
    file_bytes = await file_obj.read()
    
    # 1. EXIF
    lat, lon = get_exif_gps(file_bytes)
    if lat and lon: return lat, lon, "High Precision (EXIF)"

    # 2. Text Hint
    err_msg = ""
    if text_hint:
        lat, lon, msg = resolve_text_location(text_hint)
        if lat and lon: return lat, lon, msg
        err_msg = msg

    # 3. AI Vision
    try:
        if len(file_bytes) > 0:
            lat, lon, reason = get_ai_location_estimate(file_bytes)
            if lat and lon: return lat, lon, f"AI Vision: {reason}"
    except:
        pass

    final_msg = f"Location Failed. {err_msg}" if err_msg else "Location detection failed."
    return None, None, final_msg
