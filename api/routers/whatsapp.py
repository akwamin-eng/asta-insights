from fastapi import APIRouter, Form, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import (
    client, supabase, get_best_model, 
    save_image_from_url, format_phone_to_e164, 
    normalize_ghpostgps, enrich_listing_description, send_whatsapp_message
)
from datetime import datetime, timezone, timedelta
import re

router = APIRouter()

# --- SESSION ---
def get_session(phone: str):
    try:
        res = supabase.table("whatsapp_sessions").select("*").eq("phone_number", phone).execute()
        if res.data:
            session = res.data[0]
            last_update = datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - last_update > timedelta(hours=24):
                reset_session(phone)
                return {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}
            return session
        new_session = {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}
        supabase.table("whatsapp_sessions").insert(new_session).execute()
        return new_session
    except Exception as e:
        print(f"Session Error: {e}")
        return {"phone_number": phone, "current_step": "IDLE", "draft_data": {}}

def update_session(phone: str, step: str, data: dict):
    supabase.table("whatsapp_sessions").update({
        "current_step": step, "draft_data": data, "updated_at": "now()"
    }).eq("phone_number", phone).execute()

def reset_session(phone: str):
    supabase.table("whatsapp_sessions").update({
        "current_step": "IDLE", "draft_data": {}
    }).eq("phone_number", phone).execute()

def parse_price(price_str: str):
    """Clean 'GHS 2,500' -> 2500"""
    if not price_str: return 0
    clean = re.sub(r"[^0-9.]", "", price_str)
    try: return float(clean)
    except: return 0

# --- PUBLISHER (UPDATED FOR NEW DB SCHEMA) ---
def final_publish_task(phone: str, draft: dict):
    print(f"⚙️ Publishing for {phone}")
    try:
        enriched_desc = enrich_listing_description(draft)
        clean_price = parse_price(draft.get("price"))
        
        # New 'properties' table schema
        property_data = {
            "title": f"{draft.get('type')} in {draft.get('location')}",
            "description": draft.get("details"),
            "description_enriched": enriched_desc,
            "price": clean_price,
            "currency": "GHS",
            "type": draft.get("type", "sale").lower(),
            "status": "active",
            
            "location_name": draft.get("location"),
            "location_address": draft.get("location"),
            "location_accuracy": draft.get("location_accuracy", "low"),
            
            "vibe_features": draft.get("special_features"),
            "contact_phone": draft.get("contact"),
            "source": "whatsapp",
            "details": {
                "raw_details": draft.get("details"),
                "display_price": draft.get("price")
            }
        }
        
        # 1. Insert Property
        res = supabase.table("properties").insert(property_data).execute()
        
        if res.data:
            new_id = res.data[0]['id']
            # 2. Insert Image
            try:
                supabase.table("property_images").insert({
                    "property_id": new_id,
                    "url": draft.get("image_url"),
                    "is_hero": True
                }).execute()
            except Exception as img_e:
                print(f"Gallery Insert Error: {img_e}")
            
            # 3. Capture Email (if provided earlier in flow, or we ask now)
            # (Email capture logic is in the next step of the flow)

        live_url = "https://asta-insights.onrender.com/listings/" 
        msg = (
            f"🚀 **It's Live!**\n\n"
            f"🔗 View here: {live_url}\n\n"
            f"📈 **Stay Ahead:**\n"
            f"Reply with your **EMAIL** to get our free Market Watch report. 📧"
        )
        send_whatsapp_message(phone, msg)

    except Exception as e:
        print(f"Publish Error: {e}")
        send_whatsapp_message(phone, f"😓 System Error during publish: {str(e)}")

# --- WEBHOOK ---
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
    print(f"📩 Incoming from {From}: {Body}")
    resp = MessagingResponse()
    msg = resp.message()
    phone = From.replace("whatsapp:", "")
    
    session = get_session(phone)
    step = session.get("current_step", "IDLE")
    draft = session.get("draft_data", {}) or {}

    if Body and Body.lower() in ["cancel", "reset", "stop"]:
        reset_session(phone)
        msg.body("🔄 **Session Reset.**\n\nSend a **Photo** 📸 to start fresh!")
        return Response(content=str(resp), media_type="application/xml")

    # --- FLOW ---

    if step == "IDLE":
        if NumMedia > 0:
            msg.body("📥 Saving cover image...")
            perm_url, error_msg = save_image_from_url(MediaUrl0, phone)
            if perm_url:
                draft["image_url"] = perm_url
                msg.body("Stunning shot! 🤩 Is this for **Sale** or **Rent**?")
                update_session(phone, "AWAITING_TYPE", draft)
            else:
                msg.body(f"😓 Save Failed: {error_msg}")
        elif Body:
            msg.body("🇬🇭 **Welcome to Asta Homes!**\nSend me a **Photo** 📸 to list a property.")

    elif step == "AWAITING_TYPE":
        if Body:
            selection = Body.lower()
            draft["type"] = "Rent" if "rent" in selection else "Sale"
            msg.body(f"Got it. 💰 **What is the price?** (e.g., GHS 2000)")
            update_session(phone, "AWAITING_PRICE", draft)

    elif step == "AWAITING_PRICE":
        if Body:
            draft["price"] = Body.strip()
            msg.body("Noted. 📍 **Where is it located?**\n(Type Area Name or Send Pin)")
            update_session(phone, "AWAITING_LOCATION", draft)

    elif step == "AWAITING_LOCATION":
        if Latitude and Longitude:
            draft["location"] = f"GPS: {Latitude}, {Longitude}"
            draft["location_accuracy"] = "high"
            msg.body("✅ **GPS Pin Received.**\n\n🛏️ **Key Details?** (e.g., 2 Bed, 2 Bath)")
        elif Body:
            draft["location"] = Body.strip()
            draft["location_accuracy"] = "low"
            msg.body(f"✅ **Area:** {draft['location']}\n\n🛏️ **Key Details?** (e.g., 2 Bed, 2 Bath)")
        update_session(phone, "AWAITING_DETAILS", draft)

    elif step == "AWAITING_DETAILS":
        if Body:
            draft["details"] = Body.strip()
            msg.body("🌟 **Sell the Vibe:**\nIn one sentence, **what makes this place special?**")
            update_session(phone, "AWAITING_VIBE", draft)

    elif step == "AWAITING_VIBE":
        if Body:
            draft["special_features"] = Body.strip()
            msg.body(f"📞 Should I use **{phone}** for contact?\nReply **YES** or type number.")
            update_session(phone, "AWAITING_CONTACT", draft)

    elif step == "AWAITING_CONTACT":
        if Body:
            contact = format_phone_to_e164(phone) if "yes" in Body.lower() else format_phone_to_e164(Body.strip())
            draft["contact"] = contact
            msg.body(f"📝 **Review:**\n{draft.get('type')} in {draft.get('location')}\n💰 {draft.get('price')}\n📞 {contact}\n\nReply **YES** to publish!")
            update_session(phone, "CONFIRMATION", draft)

    elif step == "CONFIRMATION":
        if Body and "yes" in Body.lower():
            msg.body("👷‍♀️ **Generating listing...**")
            background_tasks.add_task(final_publish_task, From, draft)
            update_session(phone, "AWAITING_EMAIL", draft)
        else:
            msg.body("Reply **YES** to publish.")

    elif step == "AWAITING_EMAIL":
        if Body and "@" in Body:
            # Capture Lead
            try:
                supabase.table("leads").insert({
                    "email": Body.strip(),
                    "phone": phone,
                    "interest_area": draft.get("location"),
                    "source": "whatsapp_listing"
                }).execute()
                msg.body("📧 **Subscribed!** You're an Asta Insider.\n\nReply **PHOTO** to add more images.")
            except:
                msg.body("👍 Saved. Reply **PHOTO** to add more images.")
            reset_session(phone)
        else:
            msg.body("No problem! Reply **PHOTO** to add more images.")
            reset_session(phone)

    return Response(content=str(resp), media_type="application/xml")
