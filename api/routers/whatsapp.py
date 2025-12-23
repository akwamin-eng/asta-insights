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
            print(f"Twilio Send Error: {e}")

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    request: Request = Request
):
    if NumMedia > 0:
        send_wa_reply(From, "⏳ Asta is crafting your professional listing. One moment...")

    form_data = await request.form()
    property_id = str(uuid.uuid4())
    image_urls = []
    first_image_data = None

    # 1. Process Media
    for i in range(NumMedia):
        url = form_data.get(f'MediaUrl{i}')
        if url:
            try:
                file_bytes = download_media(url)
                if not first_image_data: first_image_data = file_bytes
                path = f"{property_id}/whatsapp_{i}.jpg"
                saved_url = await upload_image_to_supabase(file_bytes, path)
                if saved_url: image_urls.append(saved_url)
            except: continue

    if not image_urls: return "OK"

    # 2. Extract Basic Stats from Text
    price = 0
    if Body:
        nums = re.findall(r'\d+', Body.replace(',', ''))
        if nums: price = float(max([int(n) for n in nums]))

    # 3. AI COPYWRITING ENGINE (The "Top Tier" Upgrade)
    # We send the image + user text to Gemini for professional branding
    prompt = f"""
    Act as a Senior Real Estate Copywriter. Create a premium listing for Ghana's top aggregator.
    
    User Input: "{Body}"
    
    Task:
    1. Title: Create a unique, benefit-driven title (e.g. 'Contemporary 4-Bedroom Masterpiece').
    2. Description: Write a 3-paragraph professional description. Focus on lifestyle, security, and investment value.
    3. ROI Score: Assign a score (1-10) based on the image quality and description.
    4. Vibe: One word (Luxury, Coastal, Modern, etc.)
    
    Return ONLY a JSON object:
    {{"title": "...", "description": "...", "roi_score": 8.5, "vibe": "..."}}
    """
    
    try:
        # Use Gemini Vision to 'see' the property and write about it
        model = client.GenerativeModel('gemini-1.5-flash')
        # Simplified for direct bytes usage
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": first_image_data}])
        # Extract JSON from response
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(res_text)
    except Exception as e:
        print(f"AI Copywriting Error: {e}")
        ai_data = {
            "title": f"New Listing in {Body[:20] if Body else 'Accra'}", 
            "description": Body or "Beautiful property with modern finishes.",
            "roi_score": 7.0,
            "vibe": "Modern"
        }

    # 4. Save to Database
    new_prop = {
        "id": property_id,
        "title": ai_data.get("title"),
        "description": ai_data.get("description"),
        "price": price,
        "currency": "USD" if "$" in (Body or "") else "GHS",
        "image_urls": image_urls,
        "agent_id": From,
        "roi_score": ai_data.get("roi_score"),
        "vibe": ai_data.get("vibe"),
        "created_at": "now()"
    }

    try:
        supabase.table("properties").insert(new_prop).execute()
        
        web_url = f"https://asta-insights.vercel.app/listing/{property_id}"
        success_msg = f"🚀 LIVE: *{ai_data.get('title')}*\n\nYour professional listing has been generated and is now live on Asta.\n\n🔗 View Listing: {web_url}\n\nIs there a preferred WhatsApp number for buyer enquiries?"
        send_wa_reply(From, success_msg)
    except Exception as e:
        print(f"DB Error: {e}")

    return "OK"
