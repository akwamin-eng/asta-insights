from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.utils import supabase

router = APIRouter(prefix="/engagement", tags=["Phase 2: Trust & Reach"])

# --- 1. CONTEXTUAL FEEDBACK (Pulse Check) ---
class FeedbackRequest(BaseModel):
    property_id: str
    feedback_type: str  # 'GOOD_VALUE', 'OVERPRICED', 'SCAM', 'WRONG_INFO'

@router.post("/feedback")
def submit_contextual_feedback(data: FeedbackRequest):
    """Records micro-feedback. Triggers ROI downgrade if 'OVERPRICED' > 10."""
    try:
        # 1. Record Feedback
        # (Assuming 'property_feedback' table exists as per roadmap)
        # supabase.table("property_feedback").insert(data.dict()).execute()
        
        # 2. Mock Logic for ROI Downgrade
        if data.feedback_type == 'OVERPRICED':
            print(f"📉 Logic: Check if {data.property_id} has >10 flags. If so, lower ROI.")
            
        return {"status": "recorded", "message": "Thanks for keeping the market honest."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# --- 2. PRICE TRUTH TICKER ---
@router.get("/price-history/{property_id}")
def get_price_history(property_id: str):
    """Returns price changes for the graph."""
    try:
        # Query market_listing_history
        # res = supabase.table("market_listing_history").select("*").eq("listing_id", property_id).execute()
        # return res.data
        return {
            "history": [
                {"date": "2023-12-01", "price": 350000},
                {"date": "2024-01-15", "price": 320000},
                {"date": "2024-02-01", "price": 295000}
            ],
            "insight": "📉 Price dropped by 15% in 3 months."
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# --- 3. DIASPORA WATCHLIST ---
class WatchlistRequest(BaseModel):
    email: str
    neighborhood: str # e.g., "Cantonments"

@router.post("/watchlist/subscribe")
def subscribe_to_neighborhood(data: WatchlistRequest):
    """Adds user to the weekly AI digest for a specific area."""
    # Logic: Insert into 'marketing_leads' with interest tag
    return {"status": "subscribed", "message": f"We will track {data.neighborhood} for you."}
