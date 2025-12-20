# asta_data_crawler/data_sources/news_scrapers/rss_reader.py
import feedparser
import requests
from datetime import datetime, timezone
import time
import logging
from typing import List, Dict, Any
# Import the central config
from config.config import config

# Configure logger for this module
logger = logging.getLogger(__name__)

def fetch_rss_articles(feed_url: str, max_articles: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches articles from a single RSS feed URL.
    Returns a list of article dictionaries.
    """
    articles = []
    logger.info(f"  📡 Fetching RSS feed: {feed_url}")
    
    try:
        # Use requests with a timeout and headers to be respectful
        headers = {
            'User-Agent': 'ASTA Data Crawler/0.1.0 (https://github.com/akwamin-eng/asta-insights)'
        }
        response = requests.get(feed_url, headers=headers, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        # Parse the RSS feed content
        feed = feedparser.parse(response.content)
        
        if feed.bozo: # Check for feed parsing errors
             logger.warning(f"    ⚠️  Potential issue parsing feed {feed_url}: {feed.bozo_exception}")

        if not feed.entries:
            logger.info(f"    ℹ️  No entries found in feed: {feed_url}")
            return articles

        logger.info(f"    ✅ Parsed feed '{feed.feed.get('title', 'Unknown Feed')}' with {len(feed.entries)} entries.")
        
        count = 0
        for entry in feed.entries:
            if count >= max_articles:
                break
            
            try:
                # Extract article data
                article_id = entry.get('id') or entry.get('link') or f"unknown_{count}"
                # Sanitize article_id for use in filenames/DB keys if needed
                article_id_safe = article_id.replace('/', '_').replace(':', '_').replace('?', '_').replace('&', '_')[:100]

                title = entry.get('title', '').strip()
                summary = entry.get('summary', '').strip()
                # description is sometimes used instead of summary
                if not summary:
                     summary = entry.get('description', '').strip()
                
                link = entry.get('link', '').strip()
                
                # Handle published date
                published_parsed = entry.get('published_parsed')
                published_iso = ""
                if published_parsed:
                    try:
                        # feedparser usually provides a time tuple. Convert to ISO format.
                        # Assume UTC if no timezone info (common).
                        published_iso = datetime(*published_parsed[:6], tzinfo=timezone.utc).isoformat()
                    except Exception as e:
                        logger.warning(f"    ⚠️  Error parsing published date for entry in {feed_url} (ID: {article_id_safe[:30]}...): {e}")
                        # Keep published_iso as empty string or use a default?

                # --- Optional: Fetch Full Article Content ---
                # This adds significant time/network calls and complexity.
                # For now, prioritizing metadata/summary/link/published.
                # full_content = ""
                # if link:
                #     try:
                #         # Respect robots.txt and add delays
                #         time.sleep(1)
                #         article_response = requests.get(link, headers=headers, timeout=10)
                #         article_response.raise_for_status()
                #         # Use newspaper3k or similar here if needed
                #         # For simplicity, skipping full fetch for now
                #         # full_content = extract_text_from_html(article_response.text) # You'd need a function for this
                #     except Exception as e_fetch:
                #         logger.warning(f"    ⚠️  Could not fetch full article content for {link}: {e_fetch}")
                #         full_content = summary # Fallback to summary

                # Prepare data for storage
                article_data = {
                    "id": article_id_safe, # Use the safe ID
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published_iso": published_iso,
                    "feed_url": feed_url,
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                }

                articles.append(article_data)
                count += 1
                logger.debug(f"      📰 Article fetched: {title[:50]}...")

            except Exception as e_entry:
                logger.error(f"    ⚠️  Error processing entry in feed {feed_url}: {e_entry}")
                # Optionally, log the problematic entry for debugging
                # logger.debug(f"    Problematic entry: {entry}")

        logger.info(f"    📦 Fetched {len(articles)} articles from {feed_url}")

    except requests.exceptions.RequestException as e_req:
        logger.error(f"    💥 Network error fetching feed {feed_url}: {e_req}")
    except Exception as e:
        logger.error(f"    💥 Unexpected error fetching/parsing feed {feed_url}: {e}")

    return articles

def fetch_all_rss_articles(max_feeds: int = None, max_articles_per_feed: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches articles from all configured RSS feeds.
    Returns a combined list of article dictionaries.
    """
    # Use RSS feeds from central config
    all_feeds = config.RSS_FEEDS
    all_articles = []
    feeds_to_process = all_feeds[:max_feeds] if max_feeds else all_feeds
    logger.info(f"--- Starting RSS Feed Reader ---")
    logger.info(f"  Total feeds to process: {len(feeds_to_process)}")

    for i, feed_url in enumerate(feeds_to_process):
        logger.info(f"\n[{i+1}/{len(feeds_to_process)}] Processing Feed: {feed_url}")
        articles = fetch_rss_articles(feed_url, max_articles=max_articles_per_feed)
        all_articles.extend(articles)
        
        # Optional: Small delay between feeds to be respectful
        if i < len(feeds_to_process) - 1: # No need to sleep after the last one
             delay = 1.0 # seconds
             logger.debug(f"  ⏱️  Sleeping for {delay} seconds before next feed...")
             time.sleep(delay)

    logger.info(f"\n--- RSS Feed Reader Completed ---")
    logger.info(f"  Total feeds processed: {len(feeds_to_process)}")
    logger.info(f"  Total articles fetched: {len(all_articles)}")
    return all_articles

# Example usage if run directly
if __name__ == "__main__":
    # Ensure logging is configured when running directly
    import sys
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO), stream=sys.stdout)
    articles = fetch_all_rss_articles(max_feeds=2, max_articles_per_feed=5) # Fetch from first 2 feeds, max 5 articles each
    print(f"Fetched {len(articles)} articles.")
    if articles:
        print("Sample article:")
        print(articles[0])

