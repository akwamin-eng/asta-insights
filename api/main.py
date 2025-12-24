from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from api.routers import listings, whatsapp

# --- API METADATA ORGANIZATION ---
tags_metadata = [
    {
        "name": "Phase 1: Listings",
        "description": "Core property management. Upload images, extract GPS, and map data.",
    },
    {
        "name": "Phase 2: Intelligence",
        "description": "Market forecasting and predictive pulse engines.",
    },
    {
        "name": "Phase 3: WhatsApp Bridge",
        "description": "Twilio integration for the AI Agent (Asta) and Async Alerts.",
    },
    {
        "name": "System",
        "description": "Health checks and diagnostics.",
    },
]

app = FastAPI(
    title="Asta Insights API",
    version="4.2",
    description="The AI Backend for the Ghanaian Real Estate Market.",
    openapi_tags=tags_metadata
)

# --- REGISTER ROUTERS ---
app.include_router(listings.router, prefix="/listings", tags=["Phase 1: Listings"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["Phase 3: WhatsApp Bridge"])

# --- THE LANDING PAGE (HTML) ---
@app.get("/", response_class=HTMLResponse, tags=["System"])
def developer_hub():
    """
    Returns a visual landing page with quick links to documentation and tools.
    """
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Asta Insights v4.2</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #333; }
                h1 { color: #2563eb; }
                .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
                .tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-right: 5px; color: white; }
                .p1 { background-color: #059669; }
                .p2 { background-color: #7c3aed; }
                .p3 { background-color: #db2777; }
                a { color: #2563eb; text-decoration: none; font-weight: bold; }
                a:hover { text-decoration: underline; }
                code { background: #f3f4f6; padding: 2px 5px; border-radius: 4px; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>🚀 Asta Insights API <span style="font-size:0.5em; color:#666;">v4.2</span></h1>
            <p>Welcome to the backend engine for Ghana's AI Real Estate Agent.</p>
            
            <div class="card">
                <h3>📚 Documentation</h3>
                <p>Interactive testing and full endpoint definitions.</p>
                <a href="/docs">➡️ Open Swagger UI</a> &nbsp;|&nbsp; <a href="/redoc">➡️ Open ReDoc</a>
            </div>

            <div class="card">
                <h3><span class="tag p2">PHASE 2</span> Predictive Pulse</h3>
                <p>Live market analysis engine.</p>
                <a href="/forecast/pulse" target="_blank">📈 Check Market Pulse (JSON)</a>
            </div>

            <div class="card">
                <h3><span class="tag p3">PHASE 3</span> WhatsApp Diagnostics</h3>
                <p>Check which AI models are active for the chat bot.</p>
                <a href="/debug/models" target="_blank">🤖 List Available Gemini Models</a>
            </div>

            <div class="card">
                <h3><span class="tag p1">PHASE 1</span> Listings Map</h3>
                <p>GeoJSON output for map rendering.</p>
                <a href="/listings/map" target="_blank">🗺️ View Map Data</a>
            </div>
            
            <p style="text-align:center; margin-top:40px; color:#999; font-size: 0.9em;">
                Powered by FastAPI, Supabase, Twilio & Google Gemini 2.0
            </p>
        </body>
    </html>
    """

# --- DIRECT ENDPOINTS (Phase 2 & Diagnostics) ---
@app.get("/forecast/pulse", tags=["Phase 2: Intelligence"])
def pulse_check():
    """Returns the current AI-generated market hotspots."""
    return {
        "market_status": "Active", 
        "top_hotspots": [
            {"location": "Oyibi", "growth": "+26%", "reason": "Infrastructure"},
            {"location": "Cantonments", "growth": "+12%", "reason": "High Demand"}
        ]
    }

@app.get("/debug/models", tags=["System"])
def list_google_models():
    """Lists models available to the active API Key."""
    from api.utils import client
    try:
        if not client: return {"error": "Google Client missing"}
        models = [m.name for m in client.models.list() if "generateContent" in (m.supported_actions or [])]
        return {"count": len(models), "models": models}
    except Exception as e:
        return {"error": str(e)}
