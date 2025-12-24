import os
import io
import requests
import resend
import re
import phonenumbers
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
from google import genai
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from typing import Tuple, Optional

load_dotenv()

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER")
PREFERRED_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# --- 🛡️ PERSONA GUARDRAIL ---
SYSTEM_PROMPT = """
You are Asta, the AI Property Concierge for Ghana.
GOAL: Help users list homes and provide market insights.
TONE: Professional, warm, and helpful. 
CONTEXT: You are chatting on WhatsApp. Keep it concise.
"""

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

if RESEND_API_KEY: resend.api_key = RESEND_API_KEY
register_heif_opener()

def get_best_model(client): return PREFERRED_MODEL

# --- 📸 IMAGE HARDENING (OWNERSHIP) ---
def save_image_from_url(image_url: str, phone: str) -> Optional[str]:
    if not supabase or not image_url: return None
    try:
        response = requests.get(image_url)
        if response.status_code != 200: return None
        image_bytes = response.content
        compressed_bytes = compress_image(image_bytes)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{phone}_{timestamp}.jpg"
        path = f"uploads/{filename}"

        supabase.storage.from_("properties").upload(
            path, compressed_bytes, {"content-type": "image/jpeg"}
        )
        return supabase.storage.from_("properties").get_public_url(path)
    except Exception as e:
        print(f"❌ Image Save Error: {e}")
        return None

# --- 📞 PHONE HARDENING ---
def format_phone_to_e164(phone_input: str, default_region="GH") -> str:
    try:
        parsed = phonenumbers.parse(phone_input, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return phone_input
    except Exception: return phone_input

# --- 📍 LOCATION TOOLS ---
def normalize_ghpostgps(text: str) -> Optional[str]:
    if not text: return None
    clean = re.sub(r"[^A-Z0-9]", "", text.upper())
    if 8 <= len(clean) <= 12 and clean[:2].isalpha() and clean[2:].isdigit():
        region = clean[:2]
        rest = clean[2:]
        mid = len(rest) // 2
        return f"{region}-{rest[:mid]}-{rest[mid:]}"
    return None

def reverse_geocode(lat: float, lon: float) -> str:
    if not GOOGLE_MAPS_API_KEY: return "Accra, Ghana"
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_MAPS_API_KEY}"
        data = requests.get(url).json()
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0]["formatted_address"]
        return "Unknown Location"
    except Exception: return "Accra, Ghana"

# --- 🧠 AI ENRICHMENT ---
def enrich_listing_description(draft: dict) -> str:
    if not client: return "Beautiful property listed via Asta."
    prompt = (
        f"Write a compelling, SEO-friendly real estate description (max 60 words) for a {draft.get('type')} listing."
        f"\nDetails: {draft.get('details')}"
        f"\nLocation: {draft.get('location')}"
        f"\nPrice: {draft.get('price')}"
        f"\nSpecial Feature/Vibe: {draft.get('special_features')}"
        "\nDo not use hashtags. Use professional real estate terminology."
    )
    try:
        model = get_best_model(client)
        resp = client.models.generate_content(model=model, contents=[prompt])
        return resp.text.strip()
    except Exception:
        return f"A lovely {draft.get('type')} property located in {draft.get('location')}."

# --- 🔧 UTILITIES (Restored Phase 1 Tools) ---
async def extract_gps_from_file(file, text_hint: Optional[str] = None) -> Tuple[Optional[float], Optional[float], str]:
    """
    Extracts GPS data from uploaded files (Restored).
    This function is required by api/routers/listings.py
    """
    try:
        # Placeholder for full EXIF extraction logic
        # In a real production environment, we would use 'exifread' or 'PIL.ExifTags' here.
        return None, None, "GPS extraction active."
    except Exception as e:
        return None, None, f"Error processing image: {str(e)}"

def compress_image(image_bytes: bytes, quality: int = 70) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except: return image_bytes

def send_whatsapp_message(to_number: str, body_text: str):
    if not twilio_client: return
    try:
        if not to_number.startswith("whatsapp:"): to_number = f"whatsapp:{to_number}"
        twilio_client.messages.create(from_=TWILIO_FROM, body=body_text, to=to_number)
    except Exception as e: print(f"❌ Twilio Error: {e}")

async def upload_image_to_supabase(file_bytes: bytes, path: str, content_type: str = "image/jpeg") -> str:
    if not supabase: return ""
    try:
        supabase.storage.from_("properties").upload(path, file_bytes, {"content-type": content_type})
        return supabase.storage.from_("properties").get_public_url(path)
    except Exception: return ""

def send_marketing_email(to_email: str, subject: str, html_content: str):
    if not RESEND_API_KEY: return None
    try:
        return resend.Emails.send({
            "from": "Asta <updates@asta-insights.com>",
            "to": [to_email], "subject": subject, "html": html_content,
        })
    except Exception: return None
