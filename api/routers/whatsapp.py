from fastapi import APIRouter, Form, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import client, supabase, get_best_model, publish_listing_background, normalize_ghpostgps
from datetime import datetime, timezone, timedelta

router = APIRouter()

# --- HELPER: SESSION MANAGEMENT ---
def get_session(phone: str):
    res = supabase.table("whatsapp_sessions").select("*").eq("phone_number", phone).execute()
    if res.data:
        session = res.data[0]
        # 24H Rule
        last_update = datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) - last_update > timedelta(hours=24):
            reset_session(phone)
            return {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}
        return session
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
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    Latitude: float = Form(None),
    Longitude: float = Form(None)
):
    print(f"📩 Incoming from {From}: {Body} | Media: {NumMedia}")
    resp = MessagingResponse()
    msg = resp.message()
    phone = From.replace("whatsapp:", "")
    
    session = get_session(phone)
    step = session.get("current_step", "IDLE")
    draft = session.get("draft_data", {}) or {}

    # COMMANDS
    if Body and Body.lower() in ["cancel", "reset", "stop"]:
        reset_session(phone)
        msg.body("🔄 Session reset.")
        return Response(content=str(resp), media_type="application/xml")

    if Body and Body.lower() == "retry" and draft:
        msg.body("🔄 Retrying...")
        background_tasks.add_task(publish_listing_background, From, draft)
        return Response(content=str(resp), media_type="application/xml")

    # --- STATE MACHINE ---

    if step == "IDLE":
        if NumMedia > 0:
            draft["image_url"] = MediaUrl0
            msg.body("📸 Photo received! Is this for **Sale** or **Rent**?")
            update_session(phone, "AWAITING_TYPE", draft)
        elif Body:
            msg.body("👋 Welcome! Please **send a photo** to start listing.")

    elif step == "AWAITING_TYPE":
        if Body:
            selection = Body.lower()
            if "rent" in selection: draft["type"] = "Rent"
            elif "sale" in selection or "sell" in selection: draft["type"] = "Sale"
            else: draft["type"] = "Sale"
            msg.body(f"Got it: {draft['type']}. 💰 **Price?** (e.g., GHS 2000)")
            update_session(phone, "AWAITING_PRICE", draft)

    elif step == "AWAITING_PRICE":
        if Body:
            draft["price"] = Body.strip()
            msg.body("📍 **Location?** (Type 'GA-183-8164' or send a GPS Pin)")
            update_session(phone, "AWAITING_LOCATION", draft)

    elif step == "AWAITING_LOCATION":
        # SCENARIO A: GPS Pin
        if Latitude and Longitude:
            draft["location"] = f"GPS: {Latitude}, {Longitude}"
            msg.body("✅ **GPS Pin Received!**")
            msg.body("🛏️ **Details?** (e.g., 2 Bed, 1 Bath)")
            update_session(phone, "AWAITING_DETAILS", draft)
            
        # SCENARIO B: Text Parsing
        elif Body:
            # 📍 USE OMNIPARSER HERE
            parsed_gps = normalize_ghpostgps(Body.strip())
            
            if parsed_gps:
                draft["location"] = parsed_gps
                msg.body(f"✅ **Ghana Post GPS detected:** {parsed_gps}")
            else:
                draft["location"] = Body.strip()
                msg.body(f"✅ Location noted: {draft['location']}")
                
            msg.body("🛏️ **Details?** (e.g., 2 Bed, 1 Bath)")
            update_session(phone, "AWAITING_DETAILS", draft)

    elif step == "AWAITING_DETAILS":
        if Body:
            draft["details"] = Body.strip()
            msg.body(f"📞 Use **{phone}** as contact? Reply **YES** or type number.")
            update_session(phone, "AWAITING_CONTACT", draft)

    elif step == "AWAITING_CONTACT":
        if Body:
            contact = phone if "yes" in Body.lower() else Body.strip()
            draft["contact"] = contact
            summary = (
                f"📝 **Review:**\n"
                f"🏠 {draft.get('type')}\n"
                f"📍 {draft.get('location')}\n"
                f"💰 {draft.get('price')}\n"
                f"📞 {contact}\n\n"
                f"Reply **YES** to publish!"
            )
            msg.body(summary)
            update_session(phone, "CONFIRMATION", draft)

    elif step == "CONFIRMATION":
        if Body and "yes" in Body.lower():
            msg.body("👷‍♀️ Sending to Asta Listings...")
            background_tasks.add_task(publish_listing_background, From, draft)
            reset_session(phone)
        else:
            msg.body("Draft saved. Reply **YES** to publish.")

    return Response(content=str(resp), media_type="application/xml")
