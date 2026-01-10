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

keywords = [
    "rent", "land", "house", "apartment", "build", "cement", 
    "landlord", "tenant", "osu", "east legon", "cantonments", 
    "airport", "kasoa", "tema", "real estate", "airbnb", "hotel"
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
            content = entry.title + " " + entry.get("summary", "")
            content_lower = content.lower()
            
            if any(word in content_lower for word in keywords):
                print(f"      💡 Insight Found: {entry.title[:30]}...")
                
                # MAPPING TO YOUR EXACT SCHEMA
                signal = {
                    "platform": "Reddit",           # Schema: platform
                    "source_id": entry.id,
                    "content": entry.title,
                    "url": entry.link,
                    "sentiment_score": 0,           # Schema: numeric (Default neutral)
                    "topics": ["Housing"],          # Schema: ARRAY (List of strings)
                    "created_at": parser.parse(entry.published).isoformat(),
                    "status": "pending_analysis"
                }
                new_signals.append(signal)
                
    except Exception as e:
        print(f"   ⚠️ Error scanning {rss_url}: {e}")

# 3. Save to Database
if new_signals:
    try:
        # Upsert based on URL to avoid duplicates
        data = supabase.table("social_signals").upsert(new_signals, on_conflict="url").execute()
        print(f"✅ Saved {len(new_signals)} new insights to database.")
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
else:
    print("✅ Scan Complete. No relevant discussions found right now.")
