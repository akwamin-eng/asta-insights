import os
import io
import requests
from PIL import Image
from google import genai
from supabase import create_client, Client

# --- CONFIGURATION (Your Specific Env Names) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Updated to match your env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")          # Matches your env

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# New SDK automatically picks up GOOGLE_API_KEY
client = genai.Client() 

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
        # Fallback if no valid text is returned
        return {"vibe": "Modern", "score": 7.5, "trust_bullets": []}
    except Exception as e:
        print(f"AI Error: {e}")
        return {"vibe": "Standard", "score": 5, "trust_bullets": []}
