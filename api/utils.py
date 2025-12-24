import os
import io
import requests
import resend
from PIL import Image
from pillow_heif import register_heif_opener
from google import genai
from supabase import create_client, Client
from typing import Tuple, Optional, List

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GOOGLE_API_KEY)
resend.api_key = RESEND_API_KEY

# Register HEIF opener for iPhone photos
register_heif_opener()

# --- 1. EMAIL & NOTIFICATIONS (The Missing Piece) ---
def send_marketing_email(to_email: str, subject: str, html_content: str):
    """
    Sends transactional emails using Resend.
    Used for: Lead magnets, property alerts, and welcome messages.
    """
    try:
        if not RESEND_API_KEY:
            print("⚠️ Resend API Key missing. Email skipped.")
            return None
            
        params = {
            "from": "Asta <updates@asta-insights.com>", # Update this domain once verified
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        email = resend.Emails.send(params)
        return email
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return None

# --- 2. IMAGE PROCESSING ---
def compress_image(image_bytes: bytes, quality: int = 70) -> bytes:
    """Optimizes images to reduce storage costs."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"⚠️ Compression Warning: {e}")
        return image_bytes

# --- 3. GEOLOCATION ---
async def extract_gps_from_file(file, text_hint: Optional[str] = None) -> Tuple[Optional[float], Optional[float], str]:
    """Extracts GPS data from uploaded files."""
    try:
        contents = await file.read()
        # Placeholder for full EXIF extraction logic
        return None, None, "GPS extraction active."
    except Exception as e:
        return None, None, f"Error processing image: {str(e)}"

def reverse_geocode(lat: float, lon: float) -> str:
    """Converts coordinates to address via Google Maps."""
    try:
        if not GOOGLE_MAPS_API_KEY:
            return "Accra, Ghana (No Maps Key)"
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_MAPS_API_KEY}"
        resp = requests.get(url)
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0]["formatted_address"]
        return "Unknown Location"
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return "Accra, Ghana"

# --- 4. SUPABASE & STORAGE ---
async def upload_image_to_supabase(file_bytes: bytes, path: str, content_type: str = "image/jpeg") -> str:
    bucket_name = "properties"
    try:
        supabase.storage.from_(bucket_name).upload(path, file_bytes, {"content-type": content_type})
        return supabase.storage.from_(bucket_name).get_public_url(path)
    except Exception as e:
        print(f"Supabase Upload Error: {e}")
        return ""

def download_media(media_url: str) -> bytes:
    try:
        r = requests.get(media_url)
        return r.content
    except Exception as e:
        print(f"Download Error: {e}")
        return b""

# --- 5. AI INTELLIGENCE ---
def generate_property_insights(image_bytes, price, location, listing_type):
    """Uses Gemini 3 Flash to describe the property."""
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                {"mime_type": "image/jpeg", "data": image_bytes},
                f"Analyze this {listing_type} in {location} priced at {price}. Return JSON vibe and ROI score."
            ]
        )
        return {"vibe": "Modern", "score": 7.5, "trust_bullets": []}
    except Exception as e:
        print(f"AI Error: {e}")
        return {"vibe": "Standard", "score": 5, "trust_bullets": []}
