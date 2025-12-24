from fastapi import FastAPI
from api.routers import listings, whatsapp
from api.utils import client

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
    return {"market_status": "Active", "top_hotspots": []}

@app.get("/debug/models")
def list_google_models():
    """
    DIAGNOSTIC: Lists all models available to your API Key.
    """
    try:
        if not client:
            return {"error": "Google Client not initialized (Check API Key)"}
        
        # List models using the new SDK syntax
        model_list = []
        for m in client.models.list():
            # We filter for 'generateContent' models only
            if "generateContent" in (m.supported_actions or []):
                model_list.append(m.name)
        
        return {
            "count": len(model_list),
            "valid_models": model_list
        }
    except Exception as e:
        return {"error": f"Failed to list models: {str(e)}"}
