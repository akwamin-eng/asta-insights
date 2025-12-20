import os
import json
import time
from dotenv import load_dotenv
from supabase import create_client
from google import genai

# 1. SETUP & CONFIGURATION
if os.path.exists(".env"):
    load_dotenv()

# Using Service Role Key to bypass RLS for backend processing
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    print("❌ Error: Missing Environment Variables.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_deep_market_context(location):
    """Gathers all available intelligence for a specific neighborhood."""
    ctx = {
        "usd_rate": 15.0,
        "neighborhood_stats": None,
        "sentiment": None
    }
    
    try:
        # A. Get latest USD/GHS Exchange Rate
        curr = supabase.table("economic_indicators").select("value").order("recorded_at", desc=True).limit(1).execute()
        if curr.data: ctx["usd_rate"] = curr.data[0]['value']

        # B. Get Neighborhood Averages & Hub Distances
        stats = supabase.table("market_insights").select("*").eq("location", location).execute()
        if stats.data: ctx["neighborhood_stats"] = stats.data[0]

        # C. Get Qualitative Sentiment (Vibes)
        sent = supabase.table("location_sentiment").select("*").eq("location", location).execute()
        if sent.data: ctx["sentiment"] = sent.data[0]
        
    except Exception as e:
        print(f"   ⚠️ Context retrieval warning for {location}: {e}")
    
    return ctx

def process_batch(limit=10):
    print(f"🚀 [Asta Brain] Processing batch of {limit} listings...")
    
    # Fetch listings that haven't been analyzed yet
    try:
        targets = supabase.table("market_listings") \
            .select("*") \
            .is_("insight_cache", "null") \
            .limit(limit).execute()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    if not targets.data:
        print("✅ No new listings to process.")
        return

    for item in targets.data:
        listing_id = item['id']
        location = item.get('location', 'Accra')
        
        # Pull all neighborhood intelligence
        ctx = get_deep_market_context(location)
        
        print(f"🧠 Analyzing: {item['title']} in {location}...")

        # Construct a high-density prompt for Gemini
        prompt = f"""
        Act as Asta, a strategic real estate AI for the Ghana market. 
        Analyze this listing using the provided market data:

        PROPERTY: {item['title']} at {item['currency']} {item['price']}
        
        MARKET DATA FOR {location}:
        - USD Rate: {ctx['usd_rate']} GHS
        - Neighborhood Avg (Sale): {ctx['neighborhood_stats'].get('avg_price_sale') if ctx['neighborhood_stats'] else 'Unknown'}
        - Distance to Airport: {ctx['neighborhood_stats'].get('airport_dist') if ctx['neighborhood_stats'] else 'Unknown'} km
        - Distance to CBD: {ctx['neighborhood_stats'].get('central_dist') if ctx['neighborhood_stats'] else 'Unknown'} km
        - Market Vibe: {ctx['sentiment'].get('key_phrases') if ctx['sentiment'] else 'Neutral'}
        - Sentiment Score: {ctx['sentiment'].get('sentiment_score') if ctx['sentiment'] else 0}

        Return ONLY a JSON object with this schema:
        {{
          "verdict": "BUY" | "WATCH" | "AVOID",
          "investment_score": 1-10,
          "valuation": "Below Market" | "Fair Value" | "Overpriced",
          "deal_highlights": ["string"],
          "investment_logic": "One paragraph of strategic advice based on infrastructure and sentiment."
        }}
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            insight_data = json.loads(response.text)

            # Save the intelligence back to the listing
            supabase.table("market_listings").update({
                "insight_cache": insight_data,
                "insight_last_updated": "now()"
            }).eq("id", listing_id).execute()
            
            print(f"   ✅ Insight Cached.")
            time.sleep(1) # Rate limiting safeguard

        except Exception as e:
            print(f"   ❌ Failed to analyze {listing_id}: {e}")

if __name__ == "__main__":
    process_batch()
