import os
import time
import json
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai import types

# Import our new scraper
from web_scrapers.news_scraper import get_real_estate_news

load_dotenv()

# Initialize Supabase
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

# Initialize Gemini
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def analyze_news_signal(title, source):
    """
    Uses Gemini to extract structured market intelligence from a headline.
    """
    prompt = f"""
    Analyze this real estate news headline: "{title}" from {source}.
    
    Return a JSON object with:
    1. "sentiment_score": A float from -1.0 (Negative) to 1.0 (Positive).
    2. "related_locations": A list of Ghana cities/neighborhoods mentioned (e.g., ["East Legon", "Accra"]).
    3. "summary": A 1-sentence analysis of how this affects property values.
    
    Output JSON ONLY.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"   ⚠️ AI Analysis Failed: {e}")
        return None

def main():
    print("📡 Scanning for Market Signals (News & Media)...")
    
    # 1. Fetch Raw News
    articles = get_real_estate_news()
    print(f"📥 Found {len(articles)} recent articles.")
    
    new_signals = 0
    
    for article in articles:
        # Check if already processed (Idempotency)
        try:
            res = supabase.table("news_articles").select("id").eq("url", article['url']).execute()
            if len(res.data) > 0:
                continue
        except:
            pass
            
        print(f"🧠 Analyzing: {article['title'][:40]}...")
        
        # 2. AI Enrichment
        analysis = analyze_news_signal(article['title'], article['source'])
        
        if analysis:
            # 3. Store in Supabase
            payload = {
                "title": article['title'],
                "url": article['url'],
                "source": article['source'],
                "published_at": article['published_at'],
                "sentiment_score": analysis.get("sentiment_score", 0),
                "summary": analysis.get("summary", ""),
                "related_locations": analysis.get("related_locations", []),
                "created_at": "now()"
            }
            
            try:
                supabase.table("news_articles").insert(payload).execute()
                new_signals += 1
                
                # OPTIONAL: Update the Location's Sentiment Score directly?
                # For now, we just store the news. The aggregation script can use this later.
                
            except Exception as e:
                print(f"   ❌ Storage Error: {e}")
        
        # Respect Rate Limits
        time.sleep(1)

    print(f"✅ Market Signals Updated: {new_signals} new insights logged.")

if __name__ == "__main__":
    main()
