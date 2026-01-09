import feedparser
import os
import time
import re
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Graceful initialization for local testing vs production
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️  Warning: Supabase Credentials not found in environment.")
    print("   Please export SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 1. INTELLIGENCE SOURCE MATRIX ---
RSS_FEEDS = [
    # > CORE NEWS
    "https://www.myjoyonline.com/feed",
    "https://ghheadlines.com/rss",
    "https://www.ghanaiantimes.com.gh/feed",
    "https://accramail.com/feed",
    "https://theheraldghana.com/feed",
    "https://jbklutse.com/feed",
    "https://akonnornews.com/feed",
    "https://ghstandard.com/feed",
    "https://adomonline.com/feed",
    "https://mfidie.com/feed",
    "https://liveghanatv.com/feed",
    "https://afiaghana.com/feed",
    "https://successafrica.info/feed",
    "https://enewsghana.com/feed",
    "https://adwoaadubianews.com/feed",
    "https://adesawyerr.com/feed",
    "https://fifty7tech.com/feed",
    "https://ghnewsfile.com/feed",
    "https://dailynewsghana.com/feed",
    "https://aptnewsghana.com/index.php/feed",
    "https://impelnews.net/feed",
    "https://housinginghana.com/feed.xml",
    "https://rss.modernghana.com/news.xml",
    "https://rss.modernghana.com/twitterfeed.xml",

    # > FINANCIAL & FOREX (Cedi/Economy)
    "https://citibusinessnews.com/feed",
    "https://www.ghanaweb.com/GhanaHomePage/business/rss.xml", 
    "https://www.businessghana.com/rss/news.php",
    "https://thebftonline.com/feed/", 
    "https://norvanreports.com/feed/", 
    "https://www.graphic.com.gh/business/business-news.feed",
]

# --- 2. SIGNAL FILTER (NOISE REDUCTION) ---
ECONOMIC_SIGNALS = [
    "cedi", "dollar", "usd", "exchange rate", "forex", "inflation", 
    "bank of ghana", "bog", "monetary policy", "interest rate", "mpc",
    "tax", "gra", "debt", "imf", "bailout", "budget", "finance", "gdp"
]

REAL_ESTATE_SIGNALS = [
    "housing", "rent", "land", "landlord", "tenant", "apartment", 
    "construction", "infrastructure", "road", "development", "project", 
    "estate", "property", "cement", "steel", "mortgage", "works and housing"
]

ALL_SIGNALS = ECONOMIC_SIGNALS + REAL_ESTATE_SIGNALS

def clean_html(html_text):
    """Strip HTML tags to store clean text."""
    if not html_text: return ""
    return BeautifulSoup(html_text, "html.parser").get_text(separator=' ').strip()

def parse_date(date_str):
    """Standardize dates to ISO format."""
    if not date_str:
        return datetime.utcnow().isoformat()
    try:
        return parser.parse(date_str).isoformat()
    except:
        return datetime.utcnow().isoformat()

def run_sentinel():
    print(f"\n📡 ASTA RSS SENTINEL INITIALIZED")
    print(f"🎯 Surveillance Scope: {len(RSS_FEEDS)} High-Fidelity Feeds")
    
    if not supabase:
        print("❌ CRITICAL: Database connection failed. Check credentials.")
        return

    total_ingested = 0
    total_scanned = 0
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"   ↳ Pinging: {feed_url}...")
            # Set timeout to prevent hanging
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                continue

            for entry in feed.entries:
                total_scanned += 1
                
                # A. Extraction
                title = entry.get('title', '').strip()
                link = entry.get('link', '')
                
                # Clean Summary
                raw_summary = entry.get('summary', '') or entry.get('description', '')
                summary = clean_html(raw_summary)[:2000] 
                
                published_at = parse_date(entry.get('published', entry.get('updated', '')))
                source_name = feed.feed.get('title', 'Unknown Source')

                # B. Signal Detection
                content_blob = (title + " " + summary).lower()
                is_relevant = any(signal in content_blob for signal in ALL_SIGNALS)
                
                if not is_relevant:
                    continue 

                # C. Deduplication
                try:
                    existing = supabase.table('market_news').select('id', count='exact').eq('url', link).execute()
                    if existing.count > 0:
                        continue 
                except Exception as e:
                    print(f"      ⚠️ DB Check Error: {e}")
                    continue

                # D. Categorization
                category = "general"
                if any(s in content_blob for s in REAL_ESTATE_SIGNALS):
                    category = "real_estate"
                elif any(s in content_blob for s in ECONOMIC_SIGNALS):
                    category = "economy"

                # E. Archive
                payload = {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": source_name,
                    "published_at": published_at,
                    "category": category,
                    "status": "pending_enrichment",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                try:
                    supabase.table('market_news').insert(payload).execute()
                    print(f"      ✅ Archived [{category.upper()}]: {title[:50]}...")
                    total_ingested += 1
                except Exception as e:
                    print(f"      ❌ DB Insert Error: {e}")

        except Exception as e:
            print(f"   ❌ Network Error on {feed_url}: {e}")

    print(f"\n🏁 MISSION COMPLETE")
    print(f"   - Scanned: {total_scanned} items")
    print(f"   - Archived: {total_ingested} new intelligence assets")

if __name__ == "__main__":
    run_sentinel()
