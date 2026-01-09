import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from supabase import create_client, Client
from dateutil import parser
import time

# --- CONFIG ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q=Ghana+Real+Estate+Economy+Infrastructure&hl=en-GH&gl=GH&ceid=GH:en"

def get_sentiment(text):
    """
    Simple keyword-based sentiment for speed.
    (In a full production version, this would call Gemini)
    """
    text = text.lower()
    positive = ['surge', 'boost', 'growth', 'rise', 'profit', 'approve', 'new', 'success', 'gain']
    negative = ['crash', 'drop', 'loss', 'delay', 'debt', 'crisis', 'collapse', 'inflation', 'ban']
    
    score = 0
    for w in positive: 
        if w in text: score += 0.2
    for w in negative: 
        if w in text: score -= 0.2
        
    return max(min(score, 1.0), -1.0) # Clamp between -1 and 1

def fetch_and_store():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: Supabase credentials missing.")
        return

    print(f"📡 Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"📰 Fetching News from: {GOOGLE_NEWS_URL}")
    try:
        response = requests.get(GOOGLE_NEWS_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return

    # Parse RSS XML
    try:
        root = ET.fromstring(response.content)
        items = root.findall('./channel/item')
        print(f"✅ Found {len(items)} articles.")
    except Exception as e:
        print(f"❌ XML Parse Error: {e}")
        return

    new_count = 0
    
    for item in items[:15]: # Process top 15
        try:
            title = item.find('title').text
            link = item.find('link').text
            pub_date_str = item.find('pubDate').text
            source = item.find('source').text if item.find('source') is not None else "Google News"
            
            # Parse Date
            published_at = parser.parse(pub_date_str).isoformat()
            
            # Generate Metadata
            sentiment = get_sentiment(title)
            
            # Upsert Data
            data = {
                "title": title,
                "summary": title, # RSS summary is often html, using title as safer default
                "url": link,
                "source": source,
                "published_at": published_at,
                "sentiment_score": sentiment,
                "category": "Real Estate" # Default category
            }

            # Check duplication by URL to avoid spam
            existing = supabase.table('market_news').select('id').eq('url', link).execute()
            
            if not existing.data:
                supabase.table('market_news').insert(data).execute()
                print(f"🔹 Saved: {title[:50]}...")
                new_count += 1
            else:
                print(f"🔸 Skipped (Duplicate): {title[:30]}...")

        except Exception as e:
            print(f"⚠️ Error processing item: {e}")
            continue

    print(f"🚀 Job Complete. {new_count} new stories added.")

if __name__ == "__main__":
    fetch_and_store()
