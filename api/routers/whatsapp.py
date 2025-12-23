from fastapi import APIRouter, Form, Request
from typing import Optional
import uuid
from api.utils import download_media, supabase, upload_image_to_supabase, generate_property_insights

router = APIRouter(prefix="/whatsapp", tags=["Phase 2: WhatsApp Bridge"])

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    request: Request = Request
):
    form_data = await request.form()
    property_id = str(uuid.uuid4())
    image_urls = []
    first_image_bytes = None

    # 1. Process Media
    for i in range(NumMedia):
        url = form_data.get(f'MediaUrl{i}')
        if url:
            try:
                file_bytes = download_media(url)
                if not first_image_bytes: first_image_bytes = file_bytes
                
                path = f"{property_id}/whatsapp_{i}.jpg"
                saved_url = await upload_image_to_supabase(file_bytes, path)
                if saved_url: image_urls.append(saved_url)
            except Exception as e:
                print(f"Media Error at index {i}: {e}")

    if not image_urls:
        return "OK"

    # 2. Extract Price (Robust logic)
    price = 0
    if Body:
        import re
        numbers = re.findall(r'\d+', Body.replace(',', ''))
        if numbers:
            # Take the largest number as the price (likely the most accurate guess)
            price = float(max([int(n) for n in numbers]))

    # 3. AI Insights (with fallback)
    try:
        insights = generate_property_insights(first_image_bytes, price, "WhatsApp", "SALE")
    except:
        insights = {"vibe": "WhatsApp Import", "score": 5, "trust_bullets": []}

    # 4. The Data Save
    new_prop = {
        "id": property_id,
        "title": (Body[:50] + "...") if Body else "New WhatsApp Listing",
        "description": Body or "Imported via WhatsApp.",
        "price": price,
        "currency": "USD" if "$" in (Body or "") else "GHS",
        "listing_type": "SALE",
        "location": "Cantonments" if "cantonments" in (Body or "").lower() else "Accra",
        "latitude": 5.5612, 
        "longitude": -0.1976,
        "image_urls": image_urls,
        "agent_id": From, # Format: whatsapp:+233243624887
        "created_at": "now()",
        "roi_score": insights.get("score", 0),
        "vibe": insights.get("vibe", "Standard")
    }

    try:
        result = supabase.table("properties").insert(new_prop).execute()
        print(f"✅ Listing Created: {property_id}")
    except Exception as e:
        print(f"❌ DATABASE INSERT FAILED: {e}")

    return "OK"
