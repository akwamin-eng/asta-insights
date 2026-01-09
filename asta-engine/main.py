from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import services
import re
import os

app = FastAPI()

# 🔒 DYNAMIC CORS SETTINGS
# Added the Cloud Run dev URL to ensure your frontend can talk to your backend
origins = [
    "http://localhost:5173",      # Vite Local Dev
    "http://127.0.0.1:5173",      # Vite Local Dev (Alternative IP)
    "https://asta.homes",         # Production
    "https://www.asta.homes",     # WWW
    "https://asta-web-dev-1074257837836.us-central1.run.app", # Cloud Run Web Instance
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],           # Relaxed for development
    allow_headers=["*"],
)

# --- MODELS ---
class TextRequest(BaseModel):
    text: str
    user_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    property_id: int
    vote_type: str  # 'confirmed', 'sus', 'scam'
    device_id: str

# --- HELPER: NLP LITE (REGEX PARSER) ---
def parse_intent(text: str):
    text = text.lower()
    intent = {
        "location": None,
        "max_price": None,
        "type": "rent"
    }

    known_locations = ["east legon", "cantonments", "osu", "labone", "airport", "oyarifa", "adenta", "dzorwulu", "abelemkpe", "tema"]
    for loc in known_locations:
        if loc in text:
            intent["location"] = loc
            break
    
    price_pattern = r'(?:under|max|budget|below|less than|limit)\s*[:]?\s*(\d+(?:,\d{3})*(?:k|000)?)'
    price_match = re.search(price_pattern, text)
    
    if price_match:
        raw_val = price_match.group(1).replace(',', '').replace('k', '000')
        try:
            intent["max_price"] = int(raw_val)
        except:
            pass 
    
    if any(x in text for x in ["buy", "sale", "purchase"]):
        intent["type"] = "sale"

    return intent

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "ASTA Engine Secure & Online", "env": os.environ.get("K_SERVICE", "local")}

@app.get("/api/trends")
def get_trends():
    return {
        "trending_tags": ["East Legon", "Cantonments", "Osu", "Airport Residential", "Oyarifa", "Spintex"]
    }

@app.post("/process")
async def process_listing(request: TextRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        data = await services.process_text_to_property(request.text)
    except Exception as e:
        print(f"❌ AI Extraction Error: {e}")
        raise HTTPException(status_code=500, detail="AI Service Interrupted")

    if not data:
        raise HTTPException(status_code=422, detail="AI could not extract valid property data")

    if request.user_id:
        data['owner_id'] = request.user_id

    try:
        saved_record = await services.save_to_db(data)
        return {"message": "Success", "data": saved_record}
    except Exception as e:
        error_msg = str(e)
        if "check_active_requirements" in error_msg:
            raise HTTPException(status_code=422, detail="Listing Rejected: Missing critical data.")
        raise HTTPException(status_code=500, detail=f"Database Error: {error_msg}")

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    column_map = {"confirmed": "votes_good", "sus": "votes_bad", "scam": "votes_scam"}
    target_column = column_map.get(feedback.vote_type)
    
    if not target_column:
        raise HTTPException(status_code=400, detail="Invalid vote type")

    try:
        existing_vote = services.supabase.table('trust_votes')\
            .select('*')\
            .eq('property_id', feedback.property_id)\
            .eq('device_id', feedback.device_id)\
            .execute()
            
        if existing_vote.data and len(existing_vote.data) > 0:
            return {"message": "Vote already recorded", "status": "duplicate"}

        services.supabase.table('trust_votes').insert({
            "property_id": feedback.property_id,
            "device_id": feedback.device_id,
            "vote_type": feedback.vote_type
        }).execute()

        response = services.supabase.table('properties')\
            .select(target_column)\
            .eq('id', feedback.property_id)\
            .execute()
        
        current_count = response.data[0].get(target_column, 0) or 0
        services.supabase.table('properties')\
            .update({target_column: current_count + 1})\
            .eq('id', feedback.property_id)\
            .execute()
            
        return {"message": "Vote recorded", "new_count": current_count + 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    incoming_msg = Body.strip()
    intent = parse_intent(incoming_msg)
    response_text = ""

    if intent["location"]:
        try:
            query = services.supabase.table('properties')\
                .select('title, price, currency, location_name')\
                .ilike('location_name', f'%{intent["location"]}%')\
                .eq('status', 'active')
            
            if intent["max_price"]:
                query = query.lte('price', intent["max_price"])

            results = query.limit(3).execute()
            listings = results.data
            
            if listings:
                response_text = f"🔎 *Found {len(listings)} listings in {intent['location'].title()}:*\n\n"
                for item in listings:
                    price = f"{item.get('currency', 'GHS')} {item['price']:,}"
                    response_text += f"🏡 *{item['title']}*\n💰 {price}\n📍 {item['location_name']}\n\n"
            else:
                response_text = f"🚫 No listings found in {intent['location'].title()} for that budget."
        except Exception:
            response_text = "⚠️ My database is syncing. Please try again soon."
    else:
        response_text = "👋 Try: *'East Legon under 5000'*"

    twiml_response = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{response_text}</Message></Response>"
    return Response(content=twiml_response, media_type="application/xml")

# --- CLOUD RUN ENTRY POINT ---
# This is the critical block for binding to the correct port
if __name__ == "__main__":
    import uvicorn
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # Must bind to 0.0.0.0 for Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=port)