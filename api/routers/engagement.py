from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from api.utils import supabase

router = APIRouter(prefix="/engagement", tags=["Phase 2: Trust & Reach"])

# --- SCHEMAS ---
class FeedbackRequest(BaseModel):
    property_id: str
    feedback_type: str

class WatchlistRequest(BaseModel):
    email: str
    neighborhood: str

# --- 1. CONTEXTUAL FEEDBACK (Live) ---
@router.post("/feedback")
def submit_contextual_feedback(data: FeedbackRequest, request: Request):
    """Records feedback. Downgrades ROI if 'OVERPRICED' flags >= 10."""
    try:
        user_ip = request.client.host if request.client else "anon"
        supabase.table("property_feedback").insert({
            "property_id": data.property_id,
            "feedback_type": data.feedback_type,
            "user_ip": user_ip
        }).execute()
        
        if data.feedback_type == 'OVERPRICED':
            count = supabase.table("property_feedback").select("id", count="exact")\
                .eq("property_id", data.property_id).eq("feedback_type", "OVERPRICED").execute().count
            
            if count == 10:
                prop = supabase.table("properties").select("roi_score").eq("id", data.property_id).single().execute()
                new_score = max(0, (prop.data.get('roi_score', 0) or 0) - 1.0)
                supabase.table("properties").update({"roi_score": new_score}).eq("id", data.property_id).execute()
                return {"status": "recorded", "action": "roi_downgraded"}

        return {"status": "recorded"}
    except Exception as e:
        print(f"Feedback Error: {e}")
        return {"status": "error"}

# --- 2. PRICE TRUTH TICKER (Mock - Phase 2.3) ---
@router.get("/price-history/{property_id}")
def get_price_history(property_id: str):
    # This remains mocked until we have historical data accumulation
    return {
        "history": [
            {"date": "2023-12-01", "price": 350000},
            {"date": "2024-01-15", "price": 320000},
            {"date": "2024-02-01", "price": 295000}
        ],
        "insight": "📉 Price dropped by 15% in 3 months."
    }

# --- 3. DIASPORA WATCHLIST (REAL) ---
@router.post("/watchlist/subscribe")
def subscribe_to_neighborhood(data: WatchlistRequest):
    """
    REAL: Adds user to the marketing_leads table for a specific area.
    """
    try:
        # Check if email format is valid (basic check)
        if "@" not in data.email:
            raise HTTPException(400, "Invalid email address")

        # Upsert: If user already watches this area, do nothing (ignore error)
        try:
            supabase.table("marketing_leads").insert({
                "email": data.email,
                "neighborhood": data.neighborhood
            }).execute()
        except Exception as insert_error:
            # Likely a duplicate constraint violation, which is fine
            if "duplicate key" in str(insert_error):
                return {"status": "subscribed", "message": "You are already watching this area."}
            raise insert_error

        return {"status": "subscribed", "message": f"We will alert you when {data.neighborhood} moves."}
    except Exception as e:
        print(f"Watchlist Error: {e}")
        return {"status": "error", "detail": "Could not subscribe"}
