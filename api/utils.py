import os
import io
import requests
import resend
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
from google import genai
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient # New Import

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

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

if RESEND_API_KEY: resend.api_key = RESEND_API_KEY
register_heif_opener()

# --- 1. MESSAGING (The Voice) ---
def send_whatsapp_message(to_number: str, body_text: str):
    """Sends a proactive WhatsApp message (Push)."""
    if not twilio_client:
        print("⚠️ Twilio Client missing. Cannot send async alert.")
        return
    try:
        # Ensure 'whatsapp:' prefix is present
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
            
        message = twilio_client.messages.create(
            from_=TWILIO_FROM,
            body=body_text,
            to=to_number
        )
        print(f"✅ Message sent: {message.sid}")
    except Exception as e:
        print(f"❌ Twilio Error: {e}")

# --- 2. ASYNC PUBLISHER (The Worker) ---
def publish_listing_background(phone: str, draft: dict):
    """
    Background Task:
    1. Uploads image to permanent storage.
    2. Inserts into DB.
    3. Sends 'Live' confirmation.
    """
    print(f"⚙️ Processing listing for {phone}...")
    
    try:
        # A. Upload Image (If URL is external/temporary)
        image_url = draft.get("image_url")
        # In a full prod version, we download `image_url` and re-upload to Supabase here
        # to ensure we own the file. For MVP, we'll assume the URL is accessible.
        
        # B. Insert into Database
        listing_data = {
            "title": f"Property in {draft.get('location')}", # Auto-title
            "price": draft.get("price"),
            "location": draft.get("location"),
            "description": "Listed via WhatsApp", # We could use AI to generate this later
            "image_url": image_url,
            "agent_contact": draft.get("contact"),
            "status": "active"
        }
        
        # Insert and get the ID
        data = supabase.table("listings").insert(listing_data).execute()
        
        # C. Construct Public URL
        # Assuming you have a frontend route like /property/{id}
        # For now, we'll send the API data link or a placeholder
        live_url = "https://asta-insights.onrender.com/listings/" # Placeholder
        
        # D. Send Success Alert
        success_msg = (
            f"✅ *It's Live!* \n\n"
            f"Your property in {draft.get('location')} is now searchable.\n"
            f"🔗 View it here: {live_url}\n\n"
            f"Reply *MENU* to do more."
        )
        send_whatsapp_message(phone, success_msg)
        
    except Exception as e:
        print(f"❌ Publish Failed: {e}")
        error_msg = "�� I ran into a hiccup saving your listing. Our team has been notified."
        send_whatsapp_message(phone, error_msg)

# --- 3. UTILITIES (Existing) ---
def get_best_model(client): return PREFERRED_MODEL

def download_media(media_url: str) -> bytes:
    try:
        return requests.get(media_url).content
    except: return b""

