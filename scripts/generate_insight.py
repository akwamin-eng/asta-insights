import os
import json
import random
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

# CONFIGURATION
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_context_data(listing):
    location = listing.get('location', 'Accra')
    # simplified for example
    currency_data = supabase.table("economic_indicators").select("value").order("recorded_at", desc=True).limit(1).execute()
    usd_rate = currency_data.data[0]['value'] if currency_data.data else 15.0
    stats = supabase.table("market_insights").select("*").eq("location", location).execute()
    news = supabase.table("news_articles").select("title").limit(3).execute()
    return usd_rate, stats.data[0] if stats.data else None, news.data

def generate_report():
    listing_response = supabase.table("market_listings").select("*").limit(20).execute()
    listing = random.choice(listing_response.data)
    usd_rate, stats, news = get_context_data(listing)

    # NEW PROMPT: Demand JSON for the Frontend
    prompt = f"""
    You are Asta, a Real Estate Investment AI. Analyze the following property and return ONLY a JSON object.
    
    PROPERTY: {listing['title']} in {listing['location']}
    PRICE: {listing['currency']} {listing['price']}
    CONTEXT: USD/GHS {usd_rate}, Market Stats: {stats}, News: {news}

    Return exactly this JSON structure:
    {{
      "verdict": "BUY" | "WATCH" | "AVOID",
      "investment_score": 0-10,
      "deal_highlights": ["3 concise bullet points"],
      "market_position": "Underpriced" | "Fair Value" | "Premium",
      "currency_risk": "Low" | "Medium" | "High",
      "analysis_summary": "One sentence summary for a busy investor."
    }}
    """

    print(f"🧠 Generating Structured Insight for: {listing['title']}...")
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'} # CRITICAL: Forces JSON output
        )
        # Parse and pretty print the JSON
        insight = json.loads(response.text)
        print("\n--- STRUCTURED OUTPUT FOR FRONTEND ---")
        print(json.dumps(insight, indent=2))
        print("---------------------------------------\n")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_report()
