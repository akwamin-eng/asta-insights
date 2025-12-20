import os
import feedparser
from dateutil import parser
from dotenv import load_dotenv
from supabase import create_client

if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RSS_URL = "https://news.google.com/rss/search?q=Ghana+Real+Estate+OR+Accra+Housing&hl=en-GH&gl=GH&ceid=GH:en"

def run():
    print("📰 Fetching Real Estate News...")
    feed = feedparser.parse(RSS_URL)
    new_count = 0
    for entry in feed.entries[:10]:
        try:
            existing = supabase.table("news_articles").select("id").eq("url", entry.link).execute()
            if existing.data: continue

            title_text = entry.title + " " + entry.description
            locations = []
            for loc in ["Osu", "Legon", "Cantonments", "Spintex", "Airport"]:
                if loc in title_text: locations.append(loc)

            supabase.table("news_articles").insert({
                "title": entry.title,
                "url": entry.link,
                "source": entry.source.get('title', 'Google News'),
                "published_at": parser.parse(entry.published).isoformat(),
                "related_locations": locations,
                "summary": entry.description
            }).execute()
            new_count += 1
        except Exception as e:
            print(f"   ⚠️ Skipping item: {e}")
    print(f"✅ News update complete. Added {new_count} articles.")

if __name__ == "__main__":
    run()
