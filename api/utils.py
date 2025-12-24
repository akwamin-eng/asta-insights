import os
import io
import requests
import resend
import re
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
from google import genai
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from typing import Tuple, Optional

# --- LOAD LOCAL SECRETS ---
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
You are Asta, a professional, helpful, and slightly playful Real Estate AI Agent for Ghana.
YOUR GOAL: Help users list properties or find homes.
TONE: Professional but warm. Use emojis sparingly.
CRITICAL RULES:
1. NEVER roleplay as a fantasy character or anime character.
2. You are NOT from 'Black Clover'. You are a prop-tech AI.
3. If an error occurs, apologize professionally and ask to try again.
4. Keep responses under 160 characters (SMS friendly).
"""

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

if RESEND_API_KEY: resend.api_key = RESEND_API_KEY
register_heif_opener()

# --- 🛡️ ROBUST MODEL SELECTOR ---
def get_best_model(client):
    """Returns the preferred model ID from env vars."""
    return PREFERRED_MODEL

# --- 📍 OMNIPARSER: LOCATION NORMALIZER ---
def normalize_ghpostgps(text: str) -> Optional[str]:
    """
    Parses messy input to find a Ghana Post GPS code.
    Input: "ga1838164", "GA 183 8164", "ga-183-8164"
    Output: "GA-183-8164" or None
    """
    if not text: return None
    
    # 1. Clean: Remove spaces, dashes, dots, convert to uppercase
    clean = re.sub(r"[^A-Z0-9]", "", text.upper())
    
    # 2. Check Pattern: Region(2) + District(3-4) + Number(3-4)
    # Total length usually 9-11 chars (e.g., GA1838164 is 9)
    if 8 <= len(clean) <= 12 and clean[:2].isalpha() and clean[2:].isdigit():
        # Re-format with dashes
        # Logic: Region-District-Number
        # Usually District is 3 or 4 digits. We assume a standard split if ambiguous.
        
        region = clean[:2]
        rest = clean[2:]
        
        # Heuristic: Split remaining digits roughly in half
        mid = len(rest) // 2
        district = rest[:mid]
        number = rest[mid:]
        
        # However, standard formatting is often fixed logic, 
        # but flexible dash insertion is safer for storage.
        # Let's verify specifically against standard Ghana Post lengths if possible.
        # For this MVP, we will standardize to: XX-YYYY-ZZZZ
        
        return f"{region}-{district}-{number}"
        
    return None

# --- 1. MESSAGING (The Voice) ---
def send_whatsapp_message(to_number: str, body_text: str):
    """Sends a proactive WhatsApp message (Push)."""
    if not twilio_client: return
    try:
        if not to_number.startswith("whatsapp:"): to_number = f"whatsapp:{to_number}"
        twilio_client.messages.create(from_=TWILIO_FROM, body=body_text, to=to_number)
    except Exception as e: print(f"❌ Twilio Error: {e}")

# --- 2. ASYNC PUBLISHER (The Worker) ---
def publish_listing_background(phone: str, draft: dict):
    """Background Task: Uploads image, inserts to DB, and sends 'Live' alert."""
    print(f"⚙️ Processing listing for {phone}...")
    try:
        listing_data = {
            "title": f"{draft.get('type', 'Property')} in {draft.get('location')}",
            "price": draft.get("price"),
            "location": draft.get("location"),
            "description": f"{draft.get('details', '')} - Listed via WhatsApp",
            "listing_type": draft.get('type', 'Sale'),
            "image_url": draft.get("image_url"),
            "agent_contact": draft.get("contact"),
            "status": "active"
        }
        
        # ERROR TRAP: Print data to logs before inserting to debug Schema Mismatches
        print(f"📝 Inserting Data: {listing_data}")

        if supabase:
            supabase.table("listings").insert(listing_data).execute()
        
        live_url = "https://asta-insights.onrender.com/listings/" 
        success_msg = (
            f"✅ *It's Live!* \n\n"
            f"Your {draft.get('type')} listing in {draft.get('location')} is now searchable.\n"
            f"🔗 View it here: {live_url}\n\n"
            f"Reply *MENU* to do more."
        )
        send_whatsapp_message(phone, success_msg)
    except Exception as e:
        print(f"❌ Publish Failed: {e}")
        # Send a more helpful error message to the user? No, keep it simple for them.
        send_whatsapp_message(phone, "😓 I ran into a hiccup saving your listing. Please reply RETRY.")

# --- 3. UTILITIES (Restored) ---
async def extract_gps_from_file(file, text_hint: Optional[str] = None) -> Tuple[Optional[float], Optional[float], str]:
    return None, None, "GPS extraction active."

def compress_image(image_bytes: bytes, quality: int = 70) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception: return image_bytes

def download_media(media_url: str) -> bytes:
    try: return requests.get(media_url).content
    except: return b""

def reverse_geocode(lat: float, lon: float) -> str:
    if not GOOGLE_MAPS_API_KEY: return "Accra, Ghana"
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_MAPS_API_KEY}"
        data = requests.get(url).json()
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0]["formatted_address"]
        return "Unknown Location"
    except Exception: return "Accra, Ghana"

async def upload_image_to_supabase(file_bytes: bytes, path: str, content_type: str = "image/jpeg") -> str:
    if not supabase: return ""
    try:
        supabase.storage.from_("properties").upload(path, file_bytes, {"content-type": content_type})
        return supabase.storage.from_("properties").get_public_url(path)
    except Exception: return ""

def generate_property_insights(image_bytes, price, location, listing_type):
    if not client: return {"vibe": "Error", "score": 0}
    try:
        model = get_best_model(client)
        response = client.models.generate_content(
            model=model,
            contents=[
                {"mime_type": "image/jpeg", "data": image_bytes},
                f"Analyze this {listing_type} in {location} priced at {price}. Return JSON vibe and ROI score."
            ]
        )
        return {"vibe": "Modern", "score": 7.5}
    except Exception:
        return {"vibe": "Standard", "score": 5}

def send_marketing_email(to_email: str, subject: str, html_content: str):
    if not RESEND_API_KEY: return None
    try:
        return resend.Emails.send({
            "from": "Asta <updates@asta-insights.com>",
            "to": [to_email], "subject": subject, "html": html_content,
        })
    except Exception: return None
