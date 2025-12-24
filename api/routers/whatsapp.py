from fastapi import APIRouter, Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import client, extract_gps_from_file, generate_property_insights

router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None)
):
    """
    The Main Ear: Listens for incoming WhatsApp messages.
    """
    print(f"📩 Incoming from {From}: {Body} | Media: {NumMedia}")

    # 1. Initialize Twilio Response
    resp = MessagingResponse()
    msg = resp.message()

    # 2. IMAGE HANDLING (User sent a photo)
    if NumMedia > 0:
        print(f"📸 Image detected: {MediaUrl0}")
        
        # In a real scenario, we download the bytes here. 
        # For this Phase 3 'Bridge Test', we will simulate the vision check.
        # We assume the image is valid to test the pipeline flow.
        
        # Simulate AI Analysis (using our utility)
        # Note: In production, we'd download MediaUrl0 to bytes first.
        ai_insight = "I see a property! (Vision analysis connected)" 
        
        msg.body(f"👀 I see you sent a photo! Analysis: {ai_insight}")
        
    # 3. TEXT HANDLING (User sent text)
    else:
        # Use Gemini Chat for a smart response
        try:
            if client:
                chat = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=f"You are Asta, a real estate AI. User said: {Body}. Reply briefly."
                )
                response_text = chat.text
            else:
                response_text = "I'm online, but my AI brain is currently rebooting."
                
            msg.body(response_text)
            
        except Exception as e:
            print(f"❌ AI Error: {e}")
            msg.body("I'm having trouble thinking right now. Try again in a moment.")

    # 4. Return XML to Twilio
    return Response(content=str(resp), media_type="application/xml")
