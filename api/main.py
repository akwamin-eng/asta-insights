from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from api.routers import listings, agent, seo, engagement, whatsapp # Added whatsapp
from api.utils import extract_gps_from_file

app = FastAPI(
    title="Asta Insights API",
    description="Phase 2 Modular Architecture",
    version="4.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL UTILS ---
@app.post("/utils/extract-gps", tags=["Utilities"])
async def extract_gps(file: UploadFile = File(...), text_hint: Optional[str] = Form(None)):
    lat, lon, msg = await extract_gps_from_file(file, text_hint)
    return {"found": lat is not None, "latitude": lat, "longitude": lon, "message": msg}

# --- REGISTER MODULES ---
app.include_router(listings.router)   # Phase 1: Listings & Maps
app.include_router(agent.router)      # Phase 1: Chat Demo
app.include_router(seo.router)        # Phase 2: SEO Engine
app.include_router(engagement.router) # Phase 2: Feedback & Email
app.include_router(whatsapp.router)   # Phase 2: WhatsApp Bridge 🆕

@app.get("/")
def read_root():
    return {
        "status": "active", 
        "version": "4.1", 
        "modules": ["Listings", "Agent", "SEO", "Engagement", "WhatsApp"]
    }
