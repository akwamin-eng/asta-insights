from fastapi import APIRouter, Form, Request
from typing import Optional
import uuid
import os
import json
import re
from twilio.rest import Client as TwilioClient
from api.utils import download_media, supabase, upload_image_to_supabase, client

router = APIRouter(prefix="/whatsapp", tags=["Phase 2: WhatsApp Bridge"])

# Twilio Config
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

def send_wa_reply(to_number, message):
    if twilio_client and TWILIO_FROM:
        try:
            twilio_client.messages.create(body=message, from_=TWILIO_FROM, to=to_number)
        except Exception as e:
            print(f"Twilio Error: {e}")

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    request: Request = Request
):
    # 1. Immediate Acknowledge
    if NumMedia > 0:
        send_wa_reply(From, "🛋️ Asta is analyzing your property details and crafting a professional listing...")

    form_data = await request.form()
    property_id = str(uuid.uuid4())
    image_urls = []
    first_image_data = None

    # 2. Process Media & Fix Rendering
    for i in range(NumMedia):
        url = form_data.get(f'MediaUrl{i}')
        if url:
            try:
                file_bytes = download_media(url)
                if not first_image_data: first_image_data = file_bytes
                path = f"{property_id}/whatsapp_{i}.jpg"
                
                # UPLOAD & GET PUBLIC URL
                supabase.storage.from_("properties").upload(path, file_bytes, {"content-type": "image/jpeg"})
                public_url = supabase.storage.from_("properties").get_public_url(path)
                image_urls.append(public_url)
            except Exception as e:
                print(f"Media fail: {e}")

    if not image_urls: return "OK"

    # 3. AI Intelligence Overhaul (Sale vs Rent + Location + Copywriting)
    prompt = f"""
    Act as a Luxury Real Estate Agent. Analyze the provided image and text: "{Body}"
    
    TASKS:
    1. Extract Price (number only).
    2. Determine Listing Type: 'SALE' or 'RENT'.
    3. Extract Location: Be specific (e.g. 'Prampram', 'East Legon'). 
    4. Create a High-End Title: Use evocative language.
    5. Professional Description: 3 paragraphs in the style of Knight Frank or Sotheby's.
    6. ROI/Trust: Generate 3 'trust_bullets' based on what you see in the photo.

    Return ONLY valid JSON:
    {{
        "title": "string",
        "description": "string",
        "price": number,
        "listing_type": "SALE" | "RENT",
        "location": "string",
        "vibe": "string",
        "roi_score": number,
        "trust_bullets": ["string"]
    }}
    """
    
    try:
        model = client.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": first_image_data}])
        ai_data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except Exception as e:
        print(f"AI Error: {e}")
        ai_data = {"title": "Modern Property", "description": Body, "price": 0, "listing_type": "SALE", "location": "Accra", "vibe": "Modern", "roi_score": 5, "trust_bullets": []}

    # 4. Save to Database (Including the missing fields)
    new_prop = {
        "id": property_id,
        "title": ai_data["title"],
        "description": ai_data["description"],
        "price": ai_data["price"] if ai_data["price"] > 0 else 0,
        "currency": "GHS" if "ghs" in (Body or "").lower() else "USD",
        "location": ai_data["location"],
        "latitude": 5.7067, # Prampram Default if needed
        "longitude": 0.1089,
        "image_urls": image_urls, # Fixed rendering array
        "agent_id": From,
        "roi_score": ai_data["roi_score"],
        "trust_bullets": ai_data["trust_bullets"],
        "vibe": ai_data["vibe"],
        "listing_type": ai_data["listing_type"],
        "created_at": "now()"
    }

    try:
        supabase.table("properties").insert(new_prop).execute()
        
        # 5. Professional Confirmation Reply
        msg = f"✅ *Listing Live: {ai_data['title']}*\n\n📍 Location: {ai_data['location']}\n💰 Price: {new_prop['currency']} {ai_data['price']}\n📋 Type: {ai_data['listing_type']}\n\nYour property is now being analyzed by our Diaspora investor network. Please confirm the best number for enquiries."
        send_wa_reply(From, msg)
    except Exception as e:
        print(f"DB Error: {e}")

    return "OK"
