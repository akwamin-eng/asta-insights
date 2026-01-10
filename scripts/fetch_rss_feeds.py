import os
import feedparser
from supabase import create_client, Client
from dateutil import parser

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials.")
    exit(1)

supabase: Client = create_client(url, key)

feeds = [
    {"name": "Joy Business", "url": "https://www.myjoyonline.com/feed/business"},
    {"name": "Citi Business", "url": "https://citibusinessnews.com/feed/"},
    {"name": "GhanaWeb Business", "url": "https://cdn.ghanaweb.com/feed/news/business.xml"}
]

for source in feeds:
    print(f"📡 Checking {source['name']}...")
    try:
        feed = feedparser.parse(source['url'])
        
        articles_batch = []
        for entry in feed.entries[:5]:
            text_to_search = (entry.title + " " + entry.get("description", "")).lower()
            keywords = ["housing", "rent", "cement", "construction", "real estate", "land", "infrastructure", "accra"]
            
            if any(k in text_to_search for k in keywords):
                article = {
                    "title": entry.title,
                    "url": entry.link,
                    "source": source['name'],
                    "published_at": parser.parse(entry.published).isoformat(),
                    "category": "Local Market",
                    "status": "pending_analysis"
                }
                articles_batch.append(article)
        
        if articles_batch:
            supabase.table("market_news").upsert(articles_batch, on_conflict="url").execute()
            print(f"   ✅ Saved {len(articles_batch)} relevant articles.")
            
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {source['name']}: {e}")

print("✅ RSS Ingestion Complete.")
