from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import client, supabase, download_media, upload_image_to_supabase, get_best_model
import json

router = APIRouter()

# --- HELPER: MANAGE SESSION STATE ---
def get_session(phone: str):
    """Fetches or creates a session for the user."""
    res = supabase.table("whatsapp_sessions").select("*").eq("phone_number", phone).execute()
    if res.data:
        return res.data[0]
    new_session = {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}
    supabase.table("whatsapp_sessions").insert(new_session).execute()
    return new_session

def update_session(phone: str, step: str, data: dict):
    supabase.table("whatsapp_sessions").update({
        "current_step": step,
        "draft_data": data,
        "updated_at": "now()"
    }).eq("phone_number", phone).execute()

def reset_session(phone: str):
    supabase.table("whatsapp_sessions").update({
        "current_step": "IDLE",
        "draft_data": {}
    }).eq("phone_number", phone).execute()

# --- MAIN WEBHOOK ---
@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None)
):
    print(f"📩 Incoming from {From}: {Body} | Media: {NumMedia}")
    
    resp = MessagingResponse()
    msg = resp.message()
    phone = From.replace("whatsapp:", "")
    
    session = get_session(phone)
    step = session.get("current_step", "IDLE")
    draft = session.get("draft_data", {}) or {}

    # GLOBAL RESET
    if Body and Body.lower() in ["cancel", "restart", "reset", "stop"]:
        reset_session(phone)
        msg.body("🛑 Reset! I've cleared the memory. Send a photo anytime to start over.")
        return Response(content=str(resp), media_type="application/xml")

    # --- 🎭 THE PLAYFUL STATE MACHINE ---

    # 1. IDLE -> START LISTING
    if step == "IDLE":
        if NumMedia > 0 and MediaUrl0:
            msg.body("Ooh, nice property! 📸 Let's find it a new owner.\n\nFirst things first: **What's the asking price?** 💰\n(e.g., GHS 500,000)")
            draft["image_url"] = MediaUrl0
            update_session(phone, "AWAITING_PRICE", draft)
        else:
            # Casual Chat Mode
            if client:
                try:
                    model = get_best_model(client)
                    chat = client.models.generate_content(
                        model=model,
                        contents=[
                            f"You are Asta, a helpful and playful real estate assistant in Ghana. User said: '{Body}'. Keep it short and fun.",
                        ]
                    )
                    msg.body(chat.text)
                except:
                    msg.body("Hey there! 👋 I'm ready to work. Send me a photo of a house to start a listing!")
            else:
                msg.body("Hey! �� Send me a photo to start listing.")

    # 2. PRICE -> LOCATION
    elif step == "AWAITING_PRICE":
        if Body:
            draft["price"] = Body.strip()
            msg.body("Got it! 💸\n\nNow, **where is this gem hidden?** 📍\n(e.g., East Legon, Cantonments)")
            update_session(phone, "AWAITING_LOCATION", draft)
        else:
            msg.body("I missed that! How much is the property going for? 💰")

    # 3. LOCATION -> CONTACT (Smart Logic)
    elif step == "AWAITING_LOCATION":
        if Body:
            draft["location"] = Body.strip()
            # UX MAGIC: Ask to use current number
            msg.body(f"Nice area! 🌳\n\nLast question: Should buyers contact you on **this WhatsApp number**?\n\nReply **YES** to use this number, or type a different Name & Number.")
            update_session(phone, "AWAITING_CONTACT", draft)
        else:
            msg.body("I need a location to put it on the map! 🗺️ Where is it?")

    # 4. CONTACT -> CONFIRMATION
    elif step == "AWAITING_CONTACT":
        if Body:
            # Smart Detection
            if "yes" in Body.lower() or "sure" in Body.lower() or "yep" in Body.lower():
                contact_info = phone
            else:
                contact_info = Body.strip()
            
            draft["contact"] = contact_info
            
            summary = (
                f"🎉 **Almost Live!** Check the details:\n\n"
                f"📍 *Where:* {draft.get('location')}\n"
                f"💰 *Price:* {draft.get('price')}\n"
                f"📞 *Contact:* {contact_info}\n\n"
                f"Reply **YES** to publish it to the world! 🚀"
            )
            msg.body(summary)
            update_session(phone, "CONFIRMATION", draft)
        else:
            msg.body("Whoops! Reply YES to use your number, or type a new one.")

    # 5. CONFIRMATION -> PUBLISH
    elif step == "CONFIRMATION":
        if Body and "yes" in Body.lower():
            msg.body("🚀 **Boom! It's Live!**\n\nYour property has been listed on Asta Insights. Good luck with the sale! 🥂\n\n(Send another photo to list more)")
            # In Phase 4, we actually INSERT into the 'listings' table here.
            reset_session(phone)
        else:
            msg.body("No worries, I haven't published it yet. Reply **YES** to confirm or **CANCEL** to start over.")

    return Response(content=str(resp), media_type="application/xml")
