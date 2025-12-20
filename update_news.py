import os
import feedparser
from dateutil import parser
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RSS_URL = "https://news.google.com/rss/search?q=Ghana+Real+Estate+OR+Accra+Housing&hl=en-GH&gl=GH&ceid=GH:en"

def run():
    print("📰 Fetching Real Estate News...")
    feed = feedparser.parse(RSS_URL)
    
    new_count = 0
    for entry in feed.entries[:10]: # Top 10 stories
        try:
            # Check if exists
            existing = supabase.table("news_articles").select("id").eq("url", entry.link).execute()
            if existing.data:
                continue

            # Basic keyword detection for location (Simple AI for now)
            title_text = entry.title + " " + entry.description
            locations = []
            if "Osu" in title_text: locations.append("Osu")
            if "Legon" in title_text: locations.append("East Legon")
            if "Cantonments" in title_text: locations.append("Cantonments")

            payload = {
                "title": entry.title,
                "url": entry.link,
                "source": entry.source.get('title', 'Google News'),
                "published_at": parser.parse(entry.published).isoformat(),
                "related_locations": locations,
                "summary": entry.description
            }
            
            supabase.table("news_articles").insert(payload).execute()
            new_count += 1
            print(f"   + Added: {entry.title[:30]}...")

        except Exception as e:
            print(f"   ⚠️ Skipped item: {e}")

    print(f"✅ News update complete. Added {new_count} articles.")

if __name__ == "__main__":
    run()
