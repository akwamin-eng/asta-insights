import os
import feedparser
from supabase import create_client, Client
from dateutil import parser
import datetime

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials.")
    exit(1)

supabase: Client = create_client(url, key)

base = "https://news.google.com/rss/search"
query = "q=Real+Estate+Ghana+Accra+market+OR+housing+OR+construction"
params = "&hl=en-GH&gl=GH&ceid=GH:en"
rss_url = f"{base}?{query}{params}"

print(f"📡 Fetching news from: {rss_url}")
feed = feedparser.parse(rss_url)

print(f"🔍 Found {len(feed.entries)} articles.")

new_articles = []
for entry in feed.entries:
    published_at = parser.parse(entry.published).isoformat()
    article = {
        "title": entry.title,
        "url": entry.link,
        "source": entry.source.title if 'source' in entry else "Google News",
        "published_at": published_at,
        "category": "Real Estate",
        "status": "pending_analysis"
    }
    new_articles.append(article)

if new_articles:
    try:
        data = supabase.table("market_news").upsert(new_articles, on_conflict="url").execute()
        print(f"✅ Successfully ingested {len(new_articles)} articles.")
    except Exception as e:
        print(f"⚠️ Error saving to Supabase: {e}")
else:
    print("No new articles found.")
