import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_market_context(location):
    """Fetches global context to feed into the LLM"""
    # Get latest USD rate
    currency = supabase.table("economic_indicators").select("value").order("recorded_at", desc=True).limit(1).execute()
    rate = currency.data[0]['value'] if currency.data else 15.0
    
    # Get neighborhood stats
    stats = supabase.table("market_insights").select("*").eq("location", location).execute()
    
    # Get latest relevant news
    news = supabase.table("news_articles").select("title").order("published_at", desc=True).limit(3).execute()
    
    return rate, stats.data[0] if stats.data else None, news.data

def process_batch(limit=5):
    # Find listings that haven't been analyzed yet
    targets = supabase.table("market_listings") \
        .select("*") \
        .is_("insight_cache", "null") \
        .limit(limit).execute()

    if not targets.data:
        print("✅ All listings have up-to-date insights.")
        return

    for item in targets.data:
        loc = item.get('location', 'Accra')
        rate, stats, news = get_market_context(loc)
        
        print(f"🧠 Processing: {item['title']}...")

        prompt = f"""
        Analyze this Ghana property and return ONLY a JSON object.
        PROPERTY: {item['title']} in {loc}
        PRICE: {item['currency']} {item['price']}
        MARKET DATA: USD/GHS {rate}, Stats: {stats}, News: {news}

        Return exactly this structure:
        {{
          "verdict": "BUY" | "WATCH" | "AVOID",
          "investment_score": 0-10,
          "deal_highlights": ["3 bullet points"],
          "market_position": "Underpriced" | "Fair Value" | "Premium",
          "currency_risk": "Low" | "Medium" | "High",
          "short_summary": "One sentence summary."
        }}
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            insight_data = json.loads(response.text)

            # Update Supabase
            supabase.table("market_listings").update({
                "insight_cache": insight_data,
                "insight_last_updated": "now()"
            }).eq("id", item['id']).execute()
            
            print(f"   ✅ Insight cached for {item['id']}")
        except Exception as e:
            print(f"   ❌ Error processing {item['id']}: {e}")

if __name__ == "__main__":
    process_batch()
