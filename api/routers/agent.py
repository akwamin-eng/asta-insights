from fastapi import APIRouter
from pydantic import BaseModel
import json
from api.utils import supabase, client

router = APIRouter(prefix="/agent", tags=["Phase 1: Agent & Demo"])

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
def chat_with_data(request: ChatRequest):
    """The Oracle Demo: Feeds live data to Gemini."""
    try:
        response = supabase.table("properties").select("title, price, listing_type, roi_score, vibe").order("created_at", desc=True).limit(10).execute()
        market_data = response.data
        
        prompt = f"""
        You are Asta, an AI Real Estate Analyst for Ghana.
        Live Data (Last 10 Listings): {json.dumps(market_data)}
        User Question: "{request.query}"
        Answer based ONLY on the data provided. Be professional.
        """
        model_response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return {"reply": model_response.text}
    except Exception as e:
        return {"reply": f"System Error: {str(e)}"}
