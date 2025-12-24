from fastapi import FastAPI
from api.routers import listings, whatsapp

app = FastAPI(
    title="Asta Insights API",
    version="4.2",
    description="AI-Powered Real Estate Intelligence for Ghana"
)

# Register Routers
app.include_router(listings.router, prefix="/listings", tags=["Listings"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])

@app.get("/")
def home():
    return {
        "status": "online",
        "version": "4.2",
        "modules": ["Forecast", "Listings", "WhatsApp", "Agent"]
    }

@app.get("/forecast/pulse")
def pulse_check():
    # Simple placeholder to keep the endpoint alive for testing
    return {
        "market_status": "Active", 
        "top_hotspots": []
    }
