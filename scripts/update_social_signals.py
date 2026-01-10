import os
import feedparser
from supabase import create_client, Client
from dateutil import parser
import datetime

# 1. Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials.")
    exit(1)

supabase: Client = create_client(url, key)

# 2. Define The Targets (Real Conversations)
rss_urls = [
    "https://www.reddit.com/r/ghana/new/.rss",
    "https://www.reddit.com/r/Accra/new/.rss"
]

# 3. Keywords to Listen For
keywords = [
    "rent", "land", "house", "apartment", "build", "cement", 
    "landlord", "tenant", "osu", "east legon", "cantonments", 
    "airport", "kasoa", "tema", "real estate", "airbnb", "hotel",
    "buy", "selling", "scam", "agent"
]

print("🎙️  Listening to the Streets (Reddit RSS)...")

new_signals = []

for rss_url in rss_urls:
    print(f"   📡 Scanning {rss_url}...")
    try:
        # Custom User-Agent to avoid blocks
        feed = feedparser.parse(rss_url, agent="AstaBot/1.0")
        
        print(f"      ↳ Found {len(feed.entries)} recent posts.")
        
        for entry in feed.entries:
            # Combine title + summary for better keyword matching
            content = entry.title + " " + entry.get("summary", "")
            content_lower = content.lower()
            
            if any(word in content_lower for word in keywords):
                print(f"      💡 Insight Found: {entry.title[:40]}...")
                
                # MAPPING TO YOUR EXACT DB SCHEMA
                signal = {
                    "platform": "Reddit",           # DB Column: platform
                    "source_id": entry.id,          # DB Column: source_id
                    "content": entry.title,         # DB Column: content
                    "url": entry.link,              # DB Column: url
                    "sentiment_score": 0,           # DB Column: sentiment_score (numeric)
                    "topics": ["Housing"],          # DB Column: topics (ARRAY)
                    "status": "pending_analysis"    # DB Column: status
                }
                new_signals.append(signal)
                
    except Exception as e:
        print(f"   ⚠️ Error scanning {rss_url}: {e}")

# 4. Save to Database
if new_signals:
    try:
        # Upsert based on URL to avoid duplicates
        data = supabase.table("social_signals").upsert(new_signals, on_conflict="url").execute()
        print(f"✅ Saved {len(new_signals)} new insights to database.")
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
else:
    print("✅ Scan Complete. No relevant discussions found right now.")
