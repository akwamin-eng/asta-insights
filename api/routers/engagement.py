from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from api.utils import supabase

router = APIRouter(prefix="/engagement", tags=["Phase 2: Trust & Reach"])

# --- SCHEMAS ---
class FeedbackRequest(BaseModel):
    property_id: str
    feedback_type: str  # 'GOOD_VALUE', 'OVERPRICED', 'SCAM', 'WRONG_INFO'

class WatchlistRequest(BaseModel):
    email: str
    neighborhood: str

# --- 1. CONTEXTUAL FEEDBACK (The Pulse Check) ---
@router.post("/feedback")
def submit_contextual_feedback(data: FeedbackRequest, request: Request):
    """
    Records micro-feedback. 
    AUTOMATION: If 'OVERPRICED' flags > 10, it automatically lowers the ROI score by 1.0.
    """
    try:
        # 1. Record the Feedback
        user_ip = request.client.host if request.client else "anon"
        
        insert_res = supabase.table("property_feedback").insert({
            "property_id": data.property_id,
            "feedback_type": data.feedback_type,
            "user_ip": user_ip
        }).execute()
        
        # 2. The "Asta Brain" Logic: Check Thresholds
        if data.feedback_type == 'OVERPRICED':
            # Count how many 'OVERPRICED' flags this property has
            count_res = supabase.table("property_feedback")\
                .select("id", count="exact")\
                .eq("property_id", data.property_id)\
                .eq("feedback_type", "OVERPRICED")\
                .execute()
            
            flag_count = count_res.count
            
            # TRIGGER: If exactly 10 flags, downgrade ROI
            if flag_count == 10:
                print(f"📉 ROI DOWNGRADE TRIGGERED for {data.property_id}")
                
                # Fetch current ROI
                prop = supabase.table("properties").select("roi_score").eq("id", data.property_id).single().execute()
                current_score = prop.data.get('roi_score', 0)
                
                # Lower by 1.0 (Min 0)
                new_score = max(0, current_score - 1.0)
                
                # Update DB
                supabase.table("properties").update({"roi_score": new_score}).eq("id", data.property_id).execute()
                return {"status": "recorded", "action": "roi_adjusted_down", "flags": flag_count}

        return {"status": "recorded", "message": "Feedback captured."}
        
    except Exception as e:
        print(f"Feedback Error: {str(e)}")
        # Don't crash the app for feedback errors
        return {"status": "error", "detail": "Could not record feedback"}

# --- 2. PRICE TRUTH TICKER ---
@router.get("/price-history/{property_id}")
def get_price_history(property_id: str):
    """Returns price changes for the graph."""
    try:
        # For now, return a standard structure. 
        # In Phase 2.2 we will automate the 'market_listing_history' population.
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
@router.post("/watchlist/subscribe")
def subscribe_to_neighborhood(data: WatchlistRequest):
    """Adds user to the weekly AI digest for a specific area."""
    try:
        # Upsert into marketing_leads (using email as key)
        # Note: This requires the marketing_leads table we designed earlier
        # For MVP, we will mock the success response until table creation
        return {"status": "subscribed", "message": f"We will track {data.neighborhood} for you."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
