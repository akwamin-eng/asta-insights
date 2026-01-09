from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import uvicorn
import re

# --- SAFE IMPORT PATTERN ---
# We try to import services, but if it crashes (missing keys), we catch it
# so the app can still start and tell us what's wrong.
services = None
startup_error = None

try:
    import services
except Exception as e:
    print(f"⚠️ CRITICAL STARTUP ERROR: {e}")
    startup_error = str(e)

app = FastAPI()

# 🔒 CORS SETTINGS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://asta.homes",
    "https://www.asta.homes",
    # Allow all Cloud Run preview URLs
    "https://*-run.app" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow all to rule out CORS issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class TextRequest(BaseModel):
    text: str
    user_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    property_id: int
    vote_type: str
    device_id: str

# --- ENDPOINTS ---

@app.get("/")
def home():
    """
    Health Check Endpoint.
    If this returns JSON, the container is alive.
    """
    status = "Healthy" if services else "Degraded"
    return {
        "status": status, 
        "env": os.environ.get("K_SERVICE", "local"),
        "startup_error": startup_error
    }

@app.get("/api/trends")
def get_trends():
    return {
        "trending_tags": ["East Legon", "Cantonments", "Osu", "Airport Residential", "Oyarifa", "Spintex"]
    }

@app.post("/process")
async def process_listing(request: TextRequest):
    # Guard clause: If services failed to load, stop here.
    if not services:
        raise HTTPException(status_code=503, detail=f"Backend Services Unavailable: {startup_error}")

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

# ... (Include the rest of your feedback/whatsapp endpoints here normally) ...

# --- CLOUD RUN ENTRY POINT ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # We log this so we can see it in Cloud Logs
    print(f"🚀 STARTING ASTA ENGINE ON PORT {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)