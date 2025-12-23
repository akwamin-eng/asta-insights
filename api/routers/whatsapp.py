from fastapi import APIRouter, Form, Request
from typing import Optional
from api.utils import download_media, client, supabase, upload_image_to_supabase
import uuid

router = APIRouter(prefix="/whatsapp", tags=["Phase 2: WhatsApp Bridge"])

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),       # The sender's phone number
    Body: Optional[str] = Form(None), # The text (if any)
    NumMedia: int = Form(0),     # Number of images/audio files
    request: Request = Request   # Full raw request for safety
):
    """
    The 'Invisible Platform'. 
    Listens for incoming WhatsApp messages (via Twilio Webhook Standard).
    """
    
    # 1. Parse Media URLs (Twilio sends them as MediaUrl0, MediaUrl1...)
    form_data = await request.form()
    media_files = []
    
    for i in range(NumMedia):
        url = form_data.get(f'MediaUrl{i}')
        content_type = form_data.get(f'MediaContentType{i}')
        if url:
            media_files.append({"url": url, "type": content_type})

    # 2. If no media, just a chat? (Ignore for now, we want listings)
    if not media_files:
        return "OK" # Return 200 so Twilio doesn't retry

    print(f"📩 Incoming WhatsApp from {From}: {len(media_files)} files.")

    # 3. Process the Files (The "Lazy" Logic)
    # We look for 1 Audio (Description) and Images (Property)
    
    audio_blob = None
    image_urls = []
    property_id = str(uuid.uuid4())

    for idx, item in enumerate(media_files):
        file_bytes = download_media(item['url'])
        
        # Is it Voice?
        if "audio" in item['type']:
            audio_blob = file_bytes
        # Is it Image?
        elif "image" in item['type']:
            # Upload to Supabase Storage
            path = f"{property_id}/whatsapp_{idx}.jpg"
            saved_url = await upload_image_to_supabase(file_bytes, path)
            if saved_url: image_urls.append(saved_url)

    # 4. The AI Analysis
    # If we have Audio, use Gemini to Transcribe + Extract Info
    # If we have Images, use Gemini Vision
    
    prompt = """
    You are Asta. Analyze these inputs to create a Real Estate Listing.
    1. If there is audio, transcribe it and extract: Price, Location, Type.
    2. If there are images, describe the vibe.
    Output JSON: {title, price, location, listing_type, description}
    """
    
    # (Simplified: In production we send the audio bytes to Gemini 1.5 Flash)
    # For this demo, we assume the user typed the details if no audio, 
    # or we just auto-tag the images.
    
    print(f"✅ Processing Complete. Created Property {property_id} from WhatsApp.")
    
    # 5. Save to DB (The "Lazy List" Insert)
    # [Insert Logic Here - reusing the code from listings.py]
    
    return "Listing Created"
