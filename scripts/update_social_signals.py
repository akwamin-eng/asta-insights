import os
import time
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai import types

# Import the scraper
from web_scrapers.social_scraper import SocialScraper

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def clean_json_text(text):
    if not text: return ""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()

def analyze_social_post(content):
    """Asks Gemini to extract location intelligence from chatter."""
    prompt = f"""
    Analyze this social media post about Ghana: 
    "{content}"
    
    Extract specific location intelligence. Return JSON ONLY with keys:
    1. "detected_location": The specific city/neighborhood (e.g. "East Legon"). Return null if generic/entire country.
    2. "sentiment_score": Float -1.0 (Negative) to 1.0 (Positive).
    3. "topics": List of tags (e.g. ["Flooding", "Rent Hikes", "Traffic"]).
    4. "summary": One short sentence on the takeaway.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(clean_json_text(response.text))
        
        # --- FIX: Handle List vs Dict ---
        if isinstance(data, list):
            if len(data) > 0:
                return data[0] # Just take the first insight
            return None
            
        return data
    except Exception as e:
        return None

def main():
    print("��️  Listening to the Streets (Social Media Scan)...")
    
    scraper = SocialScraper()
    # Scrape Reddit
    posts = scraper.scrape_reddit(limit=15)
    
    new_signals = 0
    
    for post in posts:
        # 1. Check if we already have this post
        try:
            existing = supabase.table("social_signals").select("url").eq("url", post['url']).execute()
            if len(existing.data) > 0:
                continue
        except: pass
            
        # 2. Analyze with AI
        clean_content = post['content'][:50].replace('\n', ' ')
        print(f"   🧠 Analyzing: {clean_content}...")
        
        analysis = analyze_social_post(post['content'])
        
        if analysis and isinstance(analysis, dict) and analysis.get('detected_location'):
            # 3. Save to DB
            item = {
                "platform": post['platform'],
                "source_id": post['source_id'],
                "url": post['url'],
                "content": post['content'],
                "detected_location": analysis.get('detected_location'),
                "sentiment_score": analysis.get('sentiment_score', 0),
                "topics": analysis.get('topics', []),
                "summary": analysis.get('summary', ""),
                "created_at": post['created_at']
            }
            
            try:
                supabase.table("social_signals").insert(item).execute()
                new_signals += 1
                print(f"      ✅ Signal: {analysis['detected_location']} -> {analysis['summary']}")
            except Exception as e:
                print(f"      ❌ Save Error: {e}")
        
        time.sleep(1.5) # Rate limit kindness

    print(f"\n✅ Social Scan Complete. {new_signals} new location insights found.")

if __name__ == "__main__":
    main()
