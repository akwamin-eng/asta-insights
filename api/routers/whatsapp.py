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
            # Twilio Sandbox requires 'whatsapp:' prefix for BOTH numbers
            twilio_client.messages.create(body=message, from_=TWILIO_FROM, to=to_number)
        except Exception as e:
            print(f"Twilio Send Error: {e}")

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    request: Request = Request
):
    # 1. IMMEDIATE ACKNOWLEDGEMENT (Proof of life)
    send_wa_reply(From, "🛋️ Asta is crafting your professional listing. One moment...")

    form_data = await request.form()
    property_id = str(uuid.uuid4())
    image_urls = []
    first_image_data = None

    # 2. MEDIA PROCESSING
    for i in range(NumMedia):
        url = form_data.get(f'MediaUrl{i}')
        if url:
            try:
                file_bytes = download_media(url)
                if not first_image_data: first_image_data = file_bytes
                path = f"{property_id}/whatsapp_{i}.jpg"
                supabase.storage.from_("properties").upload(path, file_bytes, {"content-type": "image/jpeg"})
                public_url = supabase.storage.from_("properties").get_public_url(path)
                image_urls.append(public_url)
            except Exception as e:
                print(f"Media download/upload failed: {e}")

    # 3. AI COPYWRITING (The Intelligence Upgrade)
    # We now pass the user's TEXT as the primary instruction
    prompt = f"""
    Act as a Luxury Real Estate Copywriter. 
    User Text: "{Body}"
    
    INSTRUCTIONS:
    1. EXTRACT: Find the exact price and location from the User Text.
    2. UNIQUE TITLE: Create a compelling title using the Location and Features. DO NOT use 'Modern Property'.
    3. PROFESSIONAL DESCRIPTION: Write 3 paragraphs describing the lifestyle and investment potential based on the photo.
    4. LISTING TYPE: Identify if it is for 'SALE' or 'RENT'.

    Return ONLY a JSON object:
    {{
        "title": "string",
        "description": "string",
        "price": number,
        "location": "string",
        "listing_type": "SALE" | "RENT",
        "roi_score": number,
        "vibe": "string",
        "trust_bullets": ["string"]
    }}
    """
    
    try:
        model = client.GenerativeModel('gemini-1.5-flash')
        # We send BOTH the image and the prompt
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": first_image_data}])
        
        # Strip markdown and parse JSON
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(clean_json)
    except Exception as e:
        print(f"AI Reasoning Error: {e}")
        # Emergency Fallback if AI fails
        ai_data = {
            "title": f"New Listing in {Body[:20] if Body else 'Accra'}",
            "description": Body or "Imported listing.",
            "price": 0,
            "location": "Accra",
            "listing_type": "SALE",
            "roi_score": 5,
            "vibe": "Standard",
            "trust_bullets": []
        }

    # 4. FINAL DATA SAVE (Ensuring Price is a Float)
    new_prop = {
        "id": property_id,
        "title": ai_data["title"],
        "description": ai_data["description"],
        "price": float(ai_data["price"]),
        "currency": "USD" if "$" in (Body or "") else "GHS",
        "location": ai_data["location"],
        "latitude": 5.7067, 
        "longitude": 0.1089,
        "image_urls": image_urls,
        "agent_id": From,
        "roi_score": ai_data["roi_score"],
        "trust_bullets": ai_data["trust_bullets"],
        "vibe": ai_data["vibe"],
        "listing_type": ai_data["listing_type"],
        "created_at": "now()"
    }

    try:
        supabase.table("properties").insert(new_prop).execute()
        
        # 5. SUCCESS NOTIFICATION
        success_msg = f"🚀 LIVE: *{ai_data['title']}*\n\n💰 Price: {new_prop['currency']} {ai_data['price']}\n📍 Location: {ai_data['location']}\n\nView it here: https://asta-insights.vercel.app/listing/{property_id}"
        send_wa_reply(From, success_msg)
    except Exception as e:
        print(f"DB Insert Error: {e}")
        send_wa_reply(From, "⚠️ Error saving your listing. Our team is investigating.")

    return "OK"
