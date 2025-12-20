import os
import json
from dotenv import load_dotenv
from supabase import create_client
from google import genai

if os.path.exists(".env"):
    load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_sentiment():
    print("📊 Analyzing Market Sentiment...")
    
    # 1. Fetch recent news and market insights
    news = supabase.table("news_articles").select("title, summary, related_locations").limit(30).execute()
    stats = supabase.table("market_insights").select("location, listing_count").execute()
    
    if not news.data:
        print("⚠️ No news articles found to analyze.")
        return

    # 2. Ask Gemini to summarize the "Mood" of the market
    prompt = f"""
    You are Asta, a Ghana Real Estate Strategist. Analyze these news items and market counts:
    NEWS: {news.data}
    COUNTS: {stats.data}

    For each major location mentioned (Osu, East Legon, Cantonments, Spintex, Airport, etc.), 
    determine the 'Investment Vibe'.
    
    Return ONLY a JSON object like this:
    {{
      "Location Name": {{
        "score": -1.0 to 1.0,
        "vibes": ["vibe1", "vibe2"],
        "summary": "One sentence about why."
      }}
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        sentiment_map = json.loads(response.text)

        for loc, info in sentiment_map.items():
            supabase.table("location_sentiment").upsert({
                "location": loc,
                "sentiment_score": info['score'],
                "key_phrases": info['vibes'],
                "last_updated": "now()"
            }, on_conflict="location").execute()
            print(f"   ✅ {loc}: {info['score']} ({', '.join(info['vibes'])})")

    except Exception as e:
        print(f"❌ Sentiment Analysis Error: {e}")

if __name__ == "__main__":
    get_sentiment()
