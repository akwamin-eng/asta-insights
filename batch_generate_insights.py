import os
import json
import time
from dotenv import load_dotenv
from supabase import create_client
from google import genai

# 1. Environment & Setup
if os.path.exists(".env"):
    load_dotenv()

# We use the Service Role Key to bypass RLS for administrative updates
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    print("❌ Critical Error: Missing Environment Variables.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_deep_context(location):
    """Gathers economic, statistical, and sentiment context for a specific location."""
    context = {"usd_rate": 15.0, "market_stats": None, "sentiment": None}
    
    try:
        # A. Latest Currency
        curr_res = supabase.table("economic_indicators").select("value").order("recorded_at", desc=True).limit(1).execute()
        if curr_res.data: context["usd_rate"] = curr_res.data[0]['value']

        # B. Neighborhood Averages
        stat_res = supabase.table("market_insights").select("*").eq("location", location).execute()
        if stat_res.data: context["market_stats"] = stat_res.data[0]

        # C. Neighborhood Sentiment (The 'Vibe')
        sent_res = supabase.table("location_sentiment").select("*").eq("location", location).execute()
        if sent_res.data: context["sentiment"] = sent_res.data[0]
        
    except Exception as e:
        print(f"⚠️ Context Warning for {location}: {e}")
    
    return context

def process_batch(limit=10):
    print(f"🚀 [Batch Start] Processing up to {limit} listings...")
    
    # Select listings that haven't been analyzed yet (insight_cache is NULL)
    try:
        targets = supabase.table("market_listings") \
            .select("*") \
            .is_("insight_cache", "null") \
            .limit(limit).execute()
    except Exception as e:
        print(f"❌ Database Select Error: {e}")
        return

    if not targets.data:
        print("✅ No listings require processing.")
        return

    for item in targets.data:
        listing_id = item['id']
        location = item.get('location', 'Accra')
        
        # Gather local intelligence
        ctx = get_deep_context(location)
        
        print(f"🧠 Generating Insight: {item['title']} ({location})...")

        # Construct the Analyst Prompt
        prompt = f"""
        Analyze this Ghana property listing as a Senior Investment Advisor.
        
        PROPERTY DATA:
        - Title: {item['title']}
        - Location: {location}
        - Price: {item['currency']} {item['price']}
        
        MARKET CONTEXT:
        - USD/GHS Rate: {ctx['usd_rate']}
        - Local Avg Price: {ctx['market_stats'].get('avg_price_sale') if ctx['market_stats'] else 'N/A'}
        - Sentiment Score: {ctx['sentiment'].get('sentiment_score') if ctx['sentiment'] else 'N/A'}
        - Sentiment Vibes: {ctx['sentiment'].get('key_phrases') if ctx['sentiment'] else 'N/A'}

        Return ONLY a JSON object with this exact structure for our frontend:
        {{
          "verdict": "BUY" | "WATCH" | "AVOID",
          "investment_score": 1-10,
          "market_position": "Underpriced" | "Fair Value" | "Premium",
          "currency_risk": "Low" | "Medium" | "High",
          "deal_highlights": ["Point 1", "Point 2", "Point 3"],
          "short_summary": "A concise, actionable one-sentence summary."
        }}
        """

        try:
            # Call Gemini with JSON constraint
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            insight_json = json.loads(response.text)

            # Update listing with the new "Brain"
            supabase.table("market_listings").update({
                "insight_cache": insight_json,
                "insight_last_updated": "now()"
            }).eq("id", listing_id).execute()
            
            print(f"   ✅ Success: Cached to Database.")
            time.sleep(1) # Gentle rate limiting

        except Exception as e:
            print(f"   ❌ Error analyzing {listing_id}: {e}")

if __name__ == "__main__":
    process_batch()
