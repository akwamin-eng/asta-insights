import os
import io
import requests
from PIL import Image
import google.generativeai as genai
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
client = genai

# --- 1. IMAGE COMPRESSION ---
def compress_image(file_bytes: bytes) -> bytes:
    """Resizes image to max 1080p width and compresses to JPEG Quality 70."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        
        base_width = 1080
        if img.size[0] > base_width:
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=70, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Compression failed: {e}")
        return file_bytes

# --- 2. SUPABASE UPLOAD ---
async def upload_image_to_supabase(file_bytes: bytes, path: str, content_type: str = "image/jpeg") -> str:
    bucket_name = "properties"
    try:
        supabase.storage.from_(bucket_name).upload(path, file_bytes, {"content-type": content_type})
        return supabase.storage.from_(bucket_name).get_public_url(path)
    except Exception as e:
        print(f"Supabase Upload Error: {e}")
        return ""

# --- 3. GPS EXTRACTION ---
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1]
    seconds = dms[2]
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

async def extract_gps_from_file(file, text_hint=None):
    try:
        contents = await file.read()
        await file.seek(0)
        image = Image.open(io.BytesIO(contents))
        exif = get_exif_data(image)
        
        lat, lon = None, None
        if "GPSInfo" in exif:
            gps_info = exif["GPSInfo"]
            if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info and \
               "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
                lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
                lon = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
                return lat, lon, "GPS found in image metadata."
    except Exception:
        pass
        
    return None, None, "No GPS found."

def reverse_geocode(lat, lon):
    return f"{lat:.4f}, {lon:.4f}"

# --- 4. AI INSIGHTS ---
def generate_property_insights(image_bytes, price, location, listing_type):
    # Mock / Simple version for utils. 
    # Real logic uses Gemini Vision.
    return {
        "vibe": "Modern",
        "score": 7.5,
        "trust_bullets": ["Verified Location", "Good Price"]
    }

# --- 5. EMAIL MARKETING (RESEND) ---
import resend
resend.api_key = RESEND_API_KEY

def send_marketing_email(to_email: str, subject: str, html_content: str):
    if not RESEND_API_KEY: return None
    try:
        params = {
            "from": "Asta Intelligence <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        return resend.Emails.send(params)
    except Exception as e:
        print(f"Email Error: {e}")
        return None

# --- 6. WHATSAPP MEDIA DOWNLOAD (THE MISSING PIECE) --- 
def download_media(media_url: str) -> bytes:
    """Downloads image or audio from a Twilio/WhatsApp URL."""
    try:
        # Note: If using Twilio, this URL might require Basic Auth if strict security is on.
        # For Sandbox, standard requests usually work.
        r = requests.get(media_url)
        return r.content
    except Exception as e:
        print(f"Download Error: {e}")
        return b""
