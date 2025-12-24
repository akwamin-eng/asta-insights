from fastapi import APIRouter, Form, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import client, supabase, get_best_model, publish_listing_background, SYSTEM_PROMPT
from datetime import datetime, timezone, timedelta
import re

router = APIRouter()

# --- HELPER: SESSION MANAGEMENT WITH 24H PURGE ---
def get_session(phone: str):
    res = supabase.table("whatsapp_sessions").select("*").eq("phone_number", phone).execute()
    
    if res.data:
        session = res.data[0]
        # ⏳ THE 24-HOUR RULE
        last_update = datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) - last_update > timedelta(hours=24):
            # Expired: Reset
            print(f"🧹 Purging expired session for {phone}")
            reset_session(phone)
            return {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}
        return session
        
    # Create new
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

# --- MAIN WEBHOOK ---
@router.post("/webhook")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    # Twilio Location Fields
    Latitude: float = Form(None),
    Longitude: float = Form(None),
    Label: str = Form(None)
):
    print(f"📩 Incoming from {From}: {Body} | Media: {NumMedia} | Loc: {Latitude},{Longitude}")
    resp = MessagingResponse()
    msg = resp.message()
    phone = From.replace("whatsapp:", "")
    
    session = get_session(phone)
    step = session.get("current_step", "IDLE")
    draft = session.get("draft_data", {}) or {}

    # GLOBAL COMMANDS
    if Body and Body.lower() in ["cancel", "reset", "stop"]:
        reset_session(phone)
        msg.body("🔄 Session reset. Send a photo to start fresh!")
        return Response(content=str(resp), media_type="application/xml")

    if Body and Body.lower() == "retry" and draft:
        msg.body("🔄 Retrying submission...")
        background_tasks.add_task(publish_listing_background, From, draft)
        return Response(content=str(resp), media_type="application/xml")

    # --- STATE MACHINE ---

    # 1. IDLE -> PHOTO
    if step == "IDLE":
        if NumMedia > 0:
            draft["image_url"] = MediaUrl0
            msg.body("📸 Photo received! Is this for **Sale** or **Rent**?")
            update_session(phone, "AWAITING_TYPE", draft)
        elif Body:
            msg.body("👋 Welcome to Asta! Please **send a photo** of the property to start listing.")

    # 2. TYPE -> PRICE
    elif step == "AWAITING_TYPE":
        if Body:
            selection = Body.lower()
            if "rent" in selection: draft["type"] = "Rent"
            elif "sale" in selection or "sell" in selection: draft["type"] = "Sale"
            else: draft["type"] = "Sale"
            
            msg.body(f"Got it: {draft['type']}. 💰 **What is the price?** (e.g., GHS 2000)")
            update_session(phone, "AWAITING_PRICE", draft)

    # 3. PRICE -> LOCATION (The Quality Gate)
    elif step == "AWAITING_PRICE":
        if Body:
            draft["price"] = Body.strip()
            # 💡 Instruct user on the 3 Location Methods
            loc_msg = (
                "📍 **Location Time!** (Accuracy is key)\n\n"
                "1. **Best:** Tap 📎 -> Location -> 'Send Your Current Location'\n"
                "2. **Good:** Type Ghana Post GPS (e.g., GA-183-8164)\n"
                "3. **Okay:** Type the Area Name (e.g., East Legon)"
            )
            msg.body(loc_msg)
            update_session(phone, "AWAITING_LOCATION", draft)

    # 4. LOCATION -> DETAILS
    elif step == "AWAITING_LOCATION":
        # SCENARIO A: User sent a PIN (Gold Standard)
        if Latitude and Longitude:
            draft["location"] = f"GPS: {Latitude}, {Longitude}"
            draft["lat"] = Latitude
            draft["long"] = Longitude
            msg.body("✅ **GPS Pin Received!** That's perfect.")
            msg.body("🛏️ **Details?** (e.g., 2 Bed, 1 Bath)")
            update_session(phone, "AWAITING_DETAILS", draft)
            
        # SCENARIO B: User sent TEXT
        elif Body:
            text_loc = Body.strip().upper()
            # Regex for Ghana Post GPS (e.g., GA-123-4567 or GA-1234-5678)
            gh_post_pattern = r"^[A-Z]{2}-\d{3,4}-\d{3,4}$"
            
            if re.match(gh_post_pattern, text_loc):
                draft["location"] = text_loc
                msg.body("✅ **Ghana Post GPS detected.**")
            else:
                draft["location"] = Body.strip()
                msg.body("✅ Location noted (Area Name).")
                
            msg.body("🛏️ **Details?** (e.g., 2 Bed, 1 Bath)")
            update_session(phone, "AWAITING_DETAILS", draft)
            
        else:
            msg.body("Please send a Location Pin 📎 or type the address.")

    # 5. DETAILS -> CONTACT
    elif step == "AWAITING_DETAILS":
        if Body:
            draft["details"] = Body.strip()
            msg.body(f"📞 Should I use **{phone}** as the contact?\nReply **YES** or type a new number.")
            update_session(phone, "AWAITING_CONTACT", draft)

    # 6. CONTACT -> CONFIRM
    elif step == "AWAITING_CONTACT":
        if Body:
            contact = phone if "yes" in Body.lower() else Body.strip()
            draft["contact"] = contact
            
            summary = (
                f"📝 **Review:**\n"
                f"🏠 {draft.get('type')}\n"
                f"📍 {draft.get('location')}\n"
                f"💰 {draft.get('price')}\n"
                f"��️ {draft.get('details')}\n"
                f"📞 {contact}\n\n"
                f"Reply **YES** to publish!"
            )
            msg.body(summary)
            update_session(phone, "CONFIRMATION", draft)

    # PUBLISH
    elif step == "CONFIRMATION":
        if Body and "yes" in Body.lower():
            msg.body("👷‍♀️ Sending to Asta Listings...")
            background_tasks.add_task(publish_listing_background, From, draft)
            reset_session(phone)
        else:
            msg.body("Draft saved. Reply **YES** to publish.")

    return Response(content=str(resp), media_type="application/xml")
