# gcp_rss_pipeline/rss_fetcher.py
import feedparser
import requests
from datetime import datetime
import json
import os
from google.cloud import storage # Make sure google-cloud-storage is in requirements.txt
import time
from dotenv import load_dotenv # Optional, for local testing

# Load environment variables if running locally
load_dotenv()

# --- Configuration ---
# TODO: Move these to Secret Manager or Environment Variables in Cloud Run Job
# IMPORTANT: Replace these placeholder URLs with actual Ghanaian news RSS feeds!
RSS_FEEDS = [
    "https://www.ghanaweb.com/RSS/News.xml", # Placeholder - CHECK IF CORRECT FEED
    "https://www.myjoyonline.com/rss.xml",   # Placeholder - CHECK IF CORRECT FEED
    # --- ADD MORE VALID RSS FEEDS FOR GHANAIAN NEWS/BUSINESS/REAL ESTATE HERE ---
    # Finding the correct RSS URLs is crucial for this to work.
    # Check the websites themselves for RSS links/icons, often in the footer or a dedicated feeds section.
    # Look for feeds related to Business, Economy, Property, or specific sections.
]

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager") # Use your bucket name
GCS_RAW_PREFIX = "raw/rss_articles"

# Initialize GCS Client
# When running on GCP, credentials are usually picked up automatically (Application Default Credentials - ADC)
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

def clean_text(text):
    """Basic text cleaning."""
    if not text:
        return ""
    # Remove extra whitespace and newlines, replace with single space
    return ' '.join(text.split())

def fetch_and_store_articles(feed_url):
    """Fetches articles from a single RSS feed and stores them in GCS."""
    print(f"Fetching articles from: {feed_url}")
    articles_stored = 0
    try:
        feed = feedparser.parse(feed_url)
        # Check for feed parsing errors reported by feedparser
        if feed.bozo:
             print(f"Warning: Potential issue parsing feed {feed_url}: {getattr(feed, 'bozo_exception', 'Unknown error')}")

        if not feed.entries:
            print(f"Warning: No entries found in feed: {feed_url}")
            return articles_stored # Return count (0)

        for entry in feed.entries:
            try:
                # Extract article data
                # Use 'link' as a fallback unique identifier if 'id' is not present
                article_id = entry.get('id') or entry.get('link')
                if not article_id:
                    print(f"Skipping entry in {feed_url} - No 'id' or 'link' found.")
                    continue

                # Sanitize article_id for use in GCS object name (remove problematic characters, limit length)
                article_id_safe = article_id.replace('/', '_').replace(':', '_').replace('?', '_').replace('&', '_').replace('#', '_')[:100]

                title = clean_text(entry.get('title', ''))
                summary = clean_text(entry.get('summary', ''))
                link = entry.get('link', '')

                # Handle published date
                published_parsed = entry.get('published_parsed')
                published_iso = ""
                if published_parsed:
                    try:
                        # feedparser usually provides a time tuple. Convert to ISO format.
                        # Assume UTC if no timezone info (common).
                        published_iso = datetime(*published_parsed[:6]).strftime('%Y-%m-%dT%H:%M:%SZ')
                    except Exception as e:
                        print(f"Warning: Error parsing published date for entry in {feed_url} (ID: {article_id_safe[:30]}...): {e}")
                        # Keep published_iso as empty string or use a default?

                # --- Optional: Fetch Full Article Content ---
                # This adds significant time/network calls and complexity.
                # For now, prioritizing metadata/summary/link/published.
                # full_content = ""
                # if link:
                #     try:
                #         # Respect robots.txt and add delays
                #         time.sleep(1)
                #         article_response = requests.get(link, headers={'User-Agent': 'ASTA-RSS-Fetcher/1.0'}, timeout=10)
                #         article_response.raise_for_status()
                #         # Use newspaper3k or similar here if needed
                #         # For simplicity, skipping full fetch for now
                #         # full_content = extract_text_from_html(article_response.text) # You'd need a function for this
                #     except Exception as e_fetch:
                #         print(f"Warning: Could not fetch full article content for {link}: {e_fetch}")
                #         full_content = summary # Fallback to summary

                # Prepare data for storage
                article_data = {
                    "id": article_id,
                    "title": title,
                    "summary": summary,
                    # "content": full_content, # Include if fetched
                    "link": link,
                    "published_iso": published_iso,
                    "feed_url": feed_url,
                    "fetched_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') # ISO format UTC timestamp
                }

                # Define GCS blob name/path with date hierarchy
                today_str = datetime.utcnow().strftime("%Y/%m/%d")
                blob_name = f"{GCS_RAW_PREFIX}/{today_str}/{article_id_safe}.json"

                # Upload to GCS
                blob = bucket.blob(blob_name)
                # Convert Python dict to JSON string and upload
                blob.upload_from_string(json.dumps(article_data, indent=2, ensure_ascii=False), content_type='application/json; charset=utf-8')
                print(f"  Uploaded article: {article_id_safe[:50]}... to gs://{GCS_BUCKET_NAME}/{blob_name}")
                articles_stored += 1

            except Exception as e_entry:
                print(f"Error processing individual entry in feed {feed_url}: {e_entry}")
                # Optionally, log the problematic entry for debugging
                # print(f"Problematic entry data: {entry}")

        print(f"Finished processing feed {feed_url}. Stored {articles_stored} articles.")

    except Exception as e_feed:
        print(f"Failed to fetch or process feed {feed_url}: {e_feed}")

    return articles_stored # Return the number of articles successfully stored from this feed


def main():
    """Main function to iterate through feeds."""
    print("--- Starting RSS Feed Fetcher ---")
    total_feeds = len(RSS_FEEDS)
    total_articles_stored = 0
    if total_feeds == 0:
        print("Warning: RSS_FEEDS list is empty. No feeds to process.")
        return

    for i, feed_url in enumerate(RSS_FEEDS):
        print(f"\n[{i+1}/{total_feeds}] Processing Feed: {feed_url}")
        articles_from_this_feed = fetch_and_store_articles(feed_url)
        total_articles_stored += articles_from_this_feed
        # Optional: Small delay between feeds to be respectful
        if i < total_feeds - 1: # No need to sleep after the last one
             print(f"  Sleeping for 2 seconds before next feed...")
             time.sleep(2)

    print(f"\n--- RSS Feed Fetcher Completed ---")
    print(f"  Total feeds processed: {total_feeds}")
    print(f"  Total articles stored: {total_articles_stored}")


if __name__ == "__main__":
    main()
