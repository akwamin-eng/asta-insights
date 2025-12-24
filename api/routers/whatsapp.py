from fastapi import APIRouter, Form, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from api.utils import (
    client, supabase, get_best_model, 
    save_image_from_url, format_phone_to_e164, 
    normalize_ghpostgps, enrich_listing_description, send_whatsapp_message
)
from datetime import datetime, timezone, timedelta

router = APIRouter()

# --- SESSION ---
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

# --- BACKGROUND WORKER (THE PUBLISHER) ---
def final_publish_task(phone: str, draft: dict):
    print(f"⚙️ Publishing for {phone}")
    
    # 1. AI Polish
    enriched_desc = enrich_listing_description(draft)
    
    # 2. Insert Listing
    listing_data = {
        "title": f"{draft.get('type')} in {draft.get('location')}",
        "price": draft.get("price"),
        "location": draft.get("location"),
        "description": draft.get("details"),
        "description_enriched": enriched_desc,
        "special_features": draft.get("special_features"),
        "listing_type": draft.get('type'),
        "image_url": draft.get("image_url"),
        "agent_contact": draft.get("contact"),
        "location_accuracy": draft.get("location_accuracy", "low"),
        "status": "active"
    }
    
    res = supabase.table("listings").insert(listing_data).execute()
    
    # 3. Insert Image to Gallery
    if res.data:
        new_id = res.data[0]['id']
        supabase.table("listing_images").insert({
            "listing_id": new_id,
            "image_url": draft.get("image_url"),
            "is_hero": True
        }).execute()
        
    # 4. Success Message + Email Upsell
    live_url = "https://asta-insights.onrender.com/listings/" 
    msg = (
        f"🚀 **It's Live!**\n\n"
        f"🔗 View here: {live_url}\n\n"
        f"📈 **Stay Ahead:**\n"
        f"Want to know when prices change in **{draft.get('location')}**?\n"
        f"Reply with your **EMAIL** to get our free Market Watch report. 📧"
    )
    send_whatsapp_message(phone, msg)

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

    # COMMANDS
    if Body and Body.lower() in ["cancel", "reset", "stop"]:
        reset_session(phone)
        msg.body("🔄 Session reset.")
        return Response(content=str(resp), media_type="application/xml")

    # --- THE CONCIERGE FLOW ---

    if step == "IDLE":
        if NumMedia > 0:
            # 📸 HERO SHOT: Download immediately (Ownership)
            msg.body("📥 Saving cover image to secure vault...")
            perm_url = save_image_from_url(MediaUrl0, phone)
            
            if perm_url:
                draft["image_url"] = perm_url
                msg.body("Stunning shot! 🤩 Is this for **Sale** or **Rent**?")
                update_session(phone, "AWAITING_TYPE", draft)
            else:
                msg.body("😓 Failed to save image. Please try again.")
        elif Body:
            # Greeting + Market Insight
            msg.body(
                "🇬🇭 **Welcome to Asta Homes!**\n"
                "I'm your AI Property Concierge.\n\n"
                "💡 *Did you know? Rental demand in Accra is up 15% this quarter.*\n\n"
                "Let's get seen. **Send me your BEST photo (Hero Shot) to start!** 📸"
            )

    elif step == "AWAITING_TYPE":
        if Body:
            selection = Body.lower()
            if "rent" in selection: draft["type"] = "Rent"
            elif "sale" in selection: draft["type"] = "Sale"
            else: draft["type"] = "Sale"
            msg.body(f"Got it. 💰 **What is the price?** (e.g., GHS 2000)")
            update_session(phone, "AWAITING_PRICE", draft)

    elif step == "AWAITING_PRICE":
        if Body:
            draft["price"] = Body.strip()
            msg.body(
                "Noted. 📍 **Where is it located?**\n\n"
                "1. **Best:** Tap 📎 -> Location -> 'Send Current Location'\n"
                "2. **Good:** Type Digital Address (GA-183...)\n"
                "3. **Easy:** Just type the **City/Area Name**"
            )
            update_session(phone, "AWAITING_LOCATION", draft)

    elif step == "AWAITING_LOCATION":
        # Pin
        if Latitude and Longitude:
            draft["location"] = f"GPS: {Latitude}, {Longitude}"
            draft["location_accuracy"] = "high"
            msg.body("✅ **GPS Pin Received!**")
        # Text
        elif Body:
            parsed = normalize_ghpostgps(Body.strip())
            if parsed:
                draft["location"] = parsed
                draft["location_accuracy"] = "medium"
                msg.body(f"✅ **Digital Address:** {parsed}")
            else:
                draft["location"] = Body.strip()
                draft["location_accuracy"] = "low"
                msg.body(f"✅ **Area:** {draft['location']} (General Area)")
        
        msg.body("🛏️ **Key Details?** (e.g., 2 Bed, 2 Bath, AC)")
        update_session(phone, "AWAITING_DETAILS", draft)

    elif step == "AWAITING_DETAILS":
        if Body:
            draft["details"] = Body.strip()
            msg.body("�� **Sell the Vibe:**\nIn one sentence, **what makes this place special?**\n(e.g., 'Walking distance to mall')")
            update_session(phone, "AWAITING_VIBE", draft)

    elif step == "AWAITING_VIBE":
        if Body:
            draft["special_features"] = Body.strip()
            # Phone Logic
            msg.body(f"📞 Should I use **{phone}** for contact?\nReply **YES** or type a different number.")
            update_session(phone, "AWAITING_CONTACT", draft)

    elif step == "AWAITING_CONTACT":
        if Body:
            if "yes" in Body.lower():
                contact = format_phone_to_e164(phone)
            else:
                contact = format_phone_to_e164(Body.strip())
            
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
            msg.body("👷‍♀️ **Generating listing...**")
            background_tasks.add_task(final_publish_task, From, draft)
            update_session(phone, "AWAITING_EMAIL", draft) # New Step: Email
        else:
            msg.body("Reply **YES** to publish.")

    elif step == "AWAITING_EMAIL":
        if Body and "@" in Body:
            # Save Email (Update the listing we just made? 
            # Ideally we'd store it in a 'users' table, but for MVP we acknowledge)
            msg.body("📧 **Subscribed!** You're an Asta Insider.\n\nReply **PHOTO** to add more images.")
            reset_session(phone)
        elif Body and "skip" in Body.lower():
            msg.body("No problem! Reply **PHOTO** to add more images.")
            reset_session(phone)
        else:
            # Just reset if they type something else
            reset_session(phone)

    return Response(content=str(resp), media_type="application/xml")
