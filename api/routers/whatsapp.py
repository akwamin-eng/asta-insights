from fastapi import APIRouter, Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import client

router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0)
):
    """
    The Main Ear: Listens for incoming WhatsApp messages.
    """
    print(f"📩 Incoming from {From}: {Body} | Media: {NumMedia}")

    # 1. Initialize Twilio Response
    resp = MessagingResponse()
    msg = resp.message()

    try:
        if not client:
            msg.body("System Error: AI Brain missing.")
            return Response(content=str(resp), media_type="application/xml")

        # 2. Define Valid Models (Based on your Debug List)
        # We use the '2.0' series which is available in your account
        primary_model = 'gemini-2.0-flash'
        backup_model = 'gemini-2.0-flash-lite' 

        response_text = ""

        if Body:
            try:
                # Attempt 1: Gemini 2.0 Flash
                chat = client.models.generate_content(
                    model=primary_model,
                    contents=[Body],
                    config={
                        'temperature': 0.7,
                        'max_output_tokens': 150,
                    }
                )
                response_text = chat.text

            except Exception as e_primary:
                print(f"⚠️ Primary Model Failed ({primary_model}): {e_primary}")
                # Attempt 2: Gemini 2.0 Flash Lite (Backup)
                try:
                    chat = client.models.generate_content(
                        model=backup_model,
                        contents=[Body]
                    )
                    response_text = chat.text
                except Exception as e_backup:
                    print(f"❌ Backup Model Failed: {e_backup}")
                    response_text = "I'm having trouble connecting to my brain right now. Please try again later."

            msg.body(response_text)
        else:
            msg.body("I saw your message, but it had no text!")

    except Exception as e:
        print(f"❌ CRITICAL ROUTER ERROR: {str(e)}")
        msg.body("Asta is currently undergoing maintenance.")

    return Response(content=str(resp), media_type="application/xml")
