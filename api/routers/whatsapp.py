from fastapi import APIRouter, Form, Request
from typing import Optional
import uuid
import os
from twilio.rest import Client as TwilioClient
from api.utils import download_media, supabase, upload_image_to_supabase, generate_property_insights

router = APIRouter(prefix="/whatsapp", tags=["Phase 2: WhatsApp Bridge"])

# Twilio Config
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

def send_wa_reply(to_number, message):
    if twilio_client and TWILIO_FROM:
        twilio_client.messages.create(body=message, from_=TWILIO_FROM, to=to_number)

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    request: Request = Request
):
    # 1. Immediate Acknowledgement
    if NumMedia > 0:
        send_wa_reply(From, "📸 Asta has received your photos. Analyzing the market value now...")

    form_data = await request.form()
    property_id = str(uuid.uuid4())
    image_urls = []
    first_image_bytes = None

    # 2. Process Media
    for i in range(NumMedia):
        url = form_data.get(f'MediaUrl{i}')
        if url:
            try:
                file_bytes = download_media(url)
                if not first_image_bytes: first_image_bytes = file_bytes
                path = f"{property_id}/whatsapp_{i}.jpg"
                saved_url = await upload_image_to_supabase(file_bytes, path)
                if saved_url: image_urls.append(saved_url)
            except: continue

    if not image_urls: return "OK"

    # 3. AI & DB Logic (Consolidated)
    price = 0
    if Body:
        import re
        nums = re.findall(r'\d+', Body.replace(',', ''))
        if nums: price = float(max([int(n) for n in nums]))

    try:
        insights = generate_property_insights(first_image_bytes, price, "WhatsApp", "SALE")
    except:
        insights = {"vibe": "Modern", "score": 7}

    new_prop = {
        "id": property_id,
        "title": (Body[:50] + "...") if Body else "WhatsApp Listing",
        "description": Body,
        "price": price,
        "currency": "USD" if "$" in (Body or "") else "GHS",
        "image_urls": image_urls,
        "agent_id": From,
        "roi_score": insights.get("score", 0),
        "vibe": insights.get("vibe", "Modern")
    }

    try:
        supabase.table("properties").insert(new_prop).execute()
        
        # 4. Success Notification & Follow-up
        web_url = f"https://asta-insights.vercel.app/listing/{property_id}"
        success_msg = f"🚀 SUCCESS! Your listing is LIVE.\n\nView it here: {web_url}\n\nPlease confirm: Is {From.replace('whatsapp:', '')} the best WhatsApp number for interested buyers to reach you?"
        send_wa_reply(From, success_msg)
        
    except Exception as e:
        send_wa_reply(From, "⚠️ Sorry, I encountered an error saving your listing. Please try again.")

    return "OK"
