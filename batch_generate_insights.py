import os
import json
from dotenv import load_dotenv
from supabase import create_client
from google import genai

if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_market_context(location):
    rate = 15.0
    try:
        currency = supabase.table("economic_indicators").select("value").order("recorded_at", desc=True).limit(1).execute()
        if currency.data: rate = currency.data[0]['value']
    except: pass
    
    stats = None
    try:
        res = supabase.table("market_insights").select("*").eq("location", location).execute()
        if res.data: stats = res.data[0]
    except: pass
    
    return rate, stats

def process_batch(limit=5):
    targets = supabase.table("market_listings").select("*").is_("insight_cache", "null").limit(limit).execute()
    if not targets.data:
        print("✅ No listings need processing.")
        return

    for item in targets.data:
        loc = item.get('location', 'Accra')
        rate, stats = get_market_context(loc)
        print(f"🧠 Analyzing: {item['title']}...")

        prompt = f"Analyze property and return JSON: {item['title']} in {loc} at {item['price']}. USD Rate: {rate}. Market Stats: {stats}"

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            supabase.table("market_listings").update({
                "insight_cache": json.loads(response.text),
                "insight_last_updated": "now()"
            }).eq("id", item['id']).execute()
            print(f"   ✅ Saved.")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    process_batch()
