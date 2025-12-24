from fastapi import APIRouter, Form, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import client, supabase, get_best_model, publish_listing_background
import json

router = APIRouter()

# --- SESSION MANAGERS ---
def get_session(phone: str):
    res = supabase.table("whatsapp_sessions").select("*").eq("phone_number", phone).execute()
    if res.data: return res.data[0]
    new_session = {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}
    supabase.table("whatsapp_sessions").insert(new_session).execute()
    return new_session

def update_session(phone: str, step: str, data: dict):
    supabase.table("whatsapp_sessions").update({
        "current_step": step, "draft_data": data, "updated_at": "now()"
    }).eq("phone_number", phone).execute()

def reset_session(phone: str):
    supabase.table("whatsapp_sessions").update({
        "current_step": "IDLE", "draft_data": {}
    }).eq("phone_number", phone).execute()

@router.post("/webhook")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks, # <--- The Magic Ingredient
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None)
):
    print(f"📩 Incoming from {From}: {Body}")
    resp = MessagingResponse()
    msg = resp.message()
    phone = From.replace("whatsapp:", "")
    
    session = get_session(phone)
    step = session.get("current_step", "IDLE")
    draft = session.get("draft_data", {}) or {}

    # RESET COMMANDS
    if Body and Body.lower() in ["cancel", "restart", "reset"]:
        reset_session(phone)
        msg.body("🔄 Memory wiped. Send a photo to start fresh!")
        return Response(content=str(resp), media_type="application/xml")

    # --- STATE MACHINE ---

    if step == "IDLE":
        if NumMedia > 0:
            msg.body("📸 Nice photo! Let's get this listed.\n\n💰 **What's the asking price?** (e.g., GHS 500k)")
            draft["image_url"] = MediaUrl0
            update_session(phone, "AWAITING_PRICE", draft)
        else:
            # Casual Conversation
            if client:
                try:
                    chat = client.models.generate_content(
                        model=get_best_model(client),
                        contents=[f"You are Asta. User said: {Body}. Reply playfully."]
                    )
                    msg.body(chat.text)
                except: msg.body("Hey! 👋 Send me a property photo to start.")
            else:
                msg.body("Hey! 👋 Send me a photo.")

    elif step == "AWAITING_PRICE":
        if Body:
            draft["price"] = Body.strip()
            msg.body("Got it. 📍 **Where is it located?**")
            update_session(phone, "AWAITING_LOCATION", draft)
        else: msg.body("I need a price! 💰")

    elif step == "AWAITING_LOCATION":
        if Body:
            draft["location"] = Body.strip()
            msg.body(f"Okay! 📞 Should I use **{phone}** as the contact number?\n\nReply **YES** or type a different number.")
            update_session(phone, "AWAITING_CONTACT", draft)
        else: msg.body("I need a location! 🗺️")

    elif step == "AWAITING_CONTACT":
        if Body:
            contact = phone if "yes" in Body.lower() else Body.strip()
            draft["contact"] = contact
            
            summary = (
                f"📝 **Summary:**\n"
                f"📍 {draft.get('location')}\n"
                f"💰 {draft.get('price')}\n"
                f"📞 {contact}\n\n"
                f"Reply **YES** to submit. I'll alert you when it's live!"
            )
            msg.body(summary)
            update_session(phone, "CONFIRMATION", draft)

    elif step == "CONFIRMATION":
        if Body and "yes" in Body.lower():
            # 1. Reply IMMEDIATELY to user
            msg.body("👷‍♀️ **On it!** I'm processing your listing now.\n\nSit tight—I'll send you the confirmation link in a moment!")
            
            # 2. Trigger BACKGROUND Task (The Heavy Lifting)
            background_tasks.add_task(publish_listing_background, From, draft)
            
            # 3. Clear Session
            reset_session(phone)
        else:
            msg.body("Cancelled. Reply YES to confirm if you change your mind.")

    return Response(content=str(resp), media_type="application/xml")
