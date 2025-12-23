from fastapi import APIRouter
from pydantic import BaseModel
from api.utils import client # Gemini Client

router = APIRouter(prefix="/seo", tags=["Phase 2: SEO & Intelligence"])

class SEORequest(BaseModel):
    raw_title: str
    location: str
    price: float
    features: list[str] = []

@router.post("/optimize")
async def optimize_listing_seo(data: SEORequest):
    """
    Generates high-ranking keywords and meta-descriptions BEFORE posting.
    """
    prompt = f"""
    Act as a Real Estate SEO Expert for Ghana.
    Optimize this listing for Google Search and Diaspora Buyers.
    
    Input:
    - Title: {data.raw_title}
    - Location: {data.location}
    - Price: {data.price}
    - Features: {", ".join(data.features)}

    Return JSON with:
    1. 'optimized_title': (Max 60 chars, include location + vibe)
    2. 'meta_description': (Click-worthy summary)
    3. 'keywords': (List of 5 tags like 'Houses for sale in East Legon')
    """
    
    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return {"status": "success", "seo_data": resp.text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
