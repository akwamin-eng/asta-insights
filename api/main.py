from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import listings, seo, engagement # Import our new modules
from api.utils import extract_gps_from_file, UploadFile, File, Form, Optional

app = FastAPI(
    title="Asta Insights API",
    description="Phase 2 Modular Architecture",
    version="4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILS (Keep these for Utils endpoint which is global) ---
@app.post("/utils/extract-gps", tags=["Utilities"])
async def extract_gps(file: UploadFile = File(...), text_hint: Optional[str] = Form(None)):
    lat, lon, msg = await extract_gps_from_file(file, text_hint)
    return {"found": lat is not None, "latitude": lat, "longitude": lon, "message": msg}

# --- REGISTER ROUTERS ---
app.include_router(listings.router)   # Phase 1 (Safe Mode)
app.include_router(seo.router)        # Phase 2 (New SEO)
app.include_router(engagement.router) # Phase 2 (Feedback/Ticker)

@app.get("/")
def read_root():
    return {
        "status": "active", 
        "architecture": "Modular V4.0", 
        "active_modules": ["Listings (Stable)", "SEO (Beta)", "Engagement (Beta)"]
    }
