# scrapers/ghanapropertycentre_scraper.py
"""
Scraper for GhanaPropertyCentre.com using Crawl4AI.
Fetches property listings for sale and rent.
Saves raw data to GCS.
Integrates Google Cloud Translation API for YouTube transcript translation.
"""

import os
import sys
import json
import asyncio
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time
import re
from typing import List, Dict, Any

# --- Crawl4AI ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# --- Google Cloud Storage ---
from google.cloud import storage

# --- Google Cloud Translation API ---
from google.cloud import translate_v2 as translate

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# --- GCS Configuration ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager")
storage_client = storage.Client()
gcs_bucket = storage_client.bucket(GCS_BUCKET_NAME)

# --- Google Cloud Translation API Client ---
translate_client = translate.Client()
print("✅ Google Cloud Translation client built using ADC.")

# --- Site Configuration ---
SITE_NAME = "ghanapropertycentre.com"
BASE_URL_SALE = "https://www.ghanapropertycentre.com/for-sale"
BASE_URL_RENT = "https://www.ghanapropertycentre.com/for-rent"

# --- Crawl4AI Configuration ---
DEFAULT_BROWSER_CONFIG = BrowserConfig(
    headless=True,
    verbose=False
)

DEFAULT_CRAWLER_CONFIG = CrawlerRunConfig(
    cache_mode="bypass", # Ensure fresh data
    word_count_threshold=10,
    # Add other default configurations as needed
)

# --- Extraction Strategy Schema ---
# Define a schema to extract property listing data
# Based on the HTML structure observed on 2025-10-13
PROPERTY_SCHEMA = {
    "name": "GhanaPropertyCentre Listings",
    "baseSelector": "div.wp-block.property.list", # Container for each property listing
    "fields": [
        {"name": "title", "selector": "div.wp-block-title h3", "type": "text"},
        {"name": "link", "selector": "div.wp-block-title a", "type": "attribute", "attribute": "href"},
        {"name": "price", "selector": "span.price:first-of-type", "type": "text"},
        {"name": "location", "selector": "address", "type": "text"},
        {"name": "bedrooms", "selector": "ul.aux-info li:nth-of-type(1) span:first-of-type", "type": "text"},
        {"name": "bathrooms", "selector": "ul.aux-info li:nth-of-type(2) span:first-of-type", "type": "text"},
        {"name": "toilets", "selector": "ul.aux-info li:nth-of-type(3) span:first-of-type", "type": "text"},
        {"name": "area_sqm", "selector": "ul.aux-info li:nth-of-type(4) span:first-of-type", "type": "text"},
        # Add more fields if needed (e.g., description, agent info)
    ]
}

def save_raw_data_to_gcs(data: List[Dict[str, Any]], listing_type: str):
    """Saves raw scraped data to GCS."""
    if not data:
        print(f"  📝 Skipping GCS save for {SITE_NAME} ({listing_type}) - No data.")
        return

    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        blob_name = f"raw/property_listings/{SITE_NAME}/{listing_type}/{timestamp}.json"
        blob = gcs_bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(data, indent=2, ensure_ascii=False), content_type='application/json; charset=utf-8')
        print(f"  ✅ Raw data saved to GCS: gs://{GCS_BUCKET_NAME}/{blob_name}")
    except Exception as e:
        print(f"  ⚠️ Failed to save raw data for {SITE_NAME} ({listing_type}) to GCS: {e}")

async def scrape_listings(url: str, listing_type: str, max_pages: int = 300) -> List[Dict[str, Any]]:
    """
    Scrapes property listings from a given URL (sale or rent) for a specified number of pages.
    Returns a list of property dictionaries.
    """
    print(f"  🕷️  Scraping {listing_type} listings from {url[:50]}...")
    
    all_properties = []
    current_page = 1
    next_page_url = url

    # Use a single browser instance for efficiency across pages
    async with AsyncWebCrawler(config=DEFAULT_BROWSER_CONFIG) as crawler:
        while current_page <= max_pages and next_page_url:
            print(f"    📄 Page {current_page}/{max_pages}: {next_page_url[:50]}...")
            
            try:
                # --- Configure CrawlerRunConfig for this page ---
                # Use JsonCssExtractionStrategy with the defined schema
                extraction_strategy = JsonCssExtractionStrategy(PROPERTY_SCHEMA)
                config = DEFAULT_CRAWLER_CONFIG.clone(extraction_strategy=extraction_strategy)
                
                # --- Run the crawl ---
                result = await crawler.arun(url=next_page_url, config=config)
                
                if result.success:
                    print(f"    ✅ Page {current_page} scraped successfully.")
                    
                    # --- Process Extracted Content ---
                    if result.extracted_content:
                        try:
                            extracted_data = json.loads(result.extracted_content)
                            if isinstance(extracted_data, list):
                                print(f"    📦 Found {len(extracted_data)} properties on page {current_page}.")
                                # Add metadata like page number, scrape time
                                for prop in extracted_data:
                                    prop['scraped_at'] = datetime.now(timezone.utc).isoformat()
                                    prop['listing_type'] = listing_type
                                    prop['source_site'] = SITE_NAME
                                all_properties.extend(extracted_data)
                            else:
                                print(f"    ⚠️  Extracted content is not a list on page {current_page}: {type(extracted_data)}")
                        except json.JSONDecodeError as je:
                            print(f"    ⚠️  JSON decode error for extracted content on page {current_page}: {je}")
                            print(f"    Raw extracted content snippet: {result.extracted_content[:200]}...")
                    else:
                        print(f"    ℹ️  No extracted content found on page {current_page}.")
                    
                    # --- Find Next Page URL ---
                    # Use the confirmed CSS class 'pagination' from the provided snippet
                    # This is highly dependent on the site's structure.
                    # Hypothetical: Look for a link with text 'Next' or an arrow icon within a pagination div.
                    # You'll need to inspect the actual HTML to find the correct selector.
                    # For ghanapropertycentre.com, the next link is often an <a> with class 'next' or text 'Next'.
                    next_page_url = None
                    if result.html:
                        from bs4 import BeautifulSoup
                        from urllib.parse import urljoin
                        soup = BeautifulSoup(result.html, 'html.parser')
                        # --- NEW: Find pagination container using confirmed class ---
                        pagination_container = soup.find('ul', class_='pagination') # Or 'ol' if it's an ordered list
                        if not pagination_container:
                             pagination_container = soup.find('div', class_='pagination') # Fallback to div if ul not found
                        if pagination_container:
                            # --- NEW: Find the 'Next' link within the container ---
                            # Look for an <a> tag inside an <li> with class 'next'
                            next_link = pagination_container.find('li', class_='next').find('a') if pagination_container.find('li', class_='next') else None
                            # If not found, look for an <a> tag with text containing 'Next'
                            if not next_link:
                                next_link = pagination_container.find('a', string=re.compile(r'Next', re.I))
                            # If still not found, look for any <a> tag with href containing 'page=' (less reliable)
                            if not next_link:
                                next_link = pagination_container.find('a', href=re.compile(r'page=', re.I))
                            
                            if next_link and next_link.get('href'):
                                next_href = next_link['href']
                                # --- NEW: Construct full URL ---
                                # Make sure it's a full URL or prepend the base URL
                                if next_href.startswith('http'):
                                    next_page_url = next_href
                                else:
                                    next_page_url = urljoin(url, next_href) # Use urljoin for robustness
                                print(f"    🔗 Found next page link: {next_page_url[:50]}...")
                            else:
                                print(f"    ℹ️  'Next' link not found in pagination container on page {current_page}.")
                        else:
                             print(f"    ℹ️  Pagination container (ul.pagination or div.pagination) not found on page {current_page}.")
                    
                    # --- TEMPORARY: Stop after one page for testing ---
                    # print(f"    ⏸️  Stopping after page {current_page} for testing. Next page logic needs implementation.")
                    # next_page_url = None # Remove this line when implementing next page logic
                    
                else:
                    print(f"    ❌ Failed to scrape page {current_page}: {result.error_message}")
                    # Stop scraping if a page fails
                    next_page_url = None
                    
            except Exception as e:
                print(f"    💥 Exception scraping page {current_page}: {e}")
                # Stop scraping if an exception occurs
                next_page_url = None
                
            # Increment page counter
            current_page += 1
            
            # Optional: Small delay between pages to be respectful
            if next_page_url:
                delay = 2.0 # seconds
                print(f"    ⏱️  Sleeping for {delay} seconds before next page...")
                await asyncio.sleep(delay)
                
    print(f"  📊 Total properties scraped for {listing_type}: {len(all_properties)}")
    return all_properties

def fetch_youtube_transcript_api(youtube_client, video_id: str) -> str:
    """
    Fetches the transcript for a given YouTube video ID using the official YouTube Data API v3.
    Attempts to find any available caption track, downloads it, parses the text, and translates it to English.
    Uses the authenticated youtube_client.
    Returns the translated transcript text or an empty string on failure.
    """
    try:
        # 1. List available captions for the video
        caption_list_request = youtube_client.captions().list(
            part='snippet',
            videoId=video_id
        )
        caption_list_response = caption_list_request.execute()

        if not caption_list_response.get('items'):
            print(f"  ℹ️  No captions found for {video_id} via API.")
            return ""

        # 2. Find the most suitable caption track ID (prefer manual, then any available)
        caption_id = None
        original_language = None
        for item in caption_list_response['items']:
            snippet = item['snippet']
            # Prefer non-auto-generated captions first
            if not snippet.get('isAutoGenerated', False):
                caption_id = item['id']
                original_language = snippet['language']
                print(f"  📜 Found manual caption in '{original_language}' for {video_id}.")
                break

        # If no manual caption found, take the first available (auto-generated)
        if not caption_id:
            for item in caption_list_response['items']:
                 snippet = item['snippet']
                 caption_id = item['id']
                 original_language = snippet['language']
                 print(f"  📜 Found auto-generated caption in '{original_language}' for {video_id} (fallback).")
                 break

        if not caption_id:
            print(f"  ℹ️  No suitable caption track found for {video_id}.")
            return ""

        # 3. Download the caption track content (SRT format)
        srt_content = youtube_client.captions().download(
            id=caption_id,
            tfmt='srt' # or '3tts' depending on preference
        ).execute()

        # 4. Parse SRT content to extract text (SRT contains timestamps, so we need to strip them)
        # This is a simple example parsing SRT; consider using an SRT library if needed
        lines = srt_content.decode('utf-8').strip().split('\n')
        transcript_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.isdigit() and i + 2 < len(lines): # Start of an SRT entry (number)
                i += 1 # Skip the number
                # Skip timestamp line (e.g., 00:01:23,456 --> 00:01:25,789)
                i += 1
                # Collect subtitle text lines (can be multiple lines per entry)
                text_lines = []
                while i < len(lines) and lines[i].strip() != "":
                    text_lines.append(lines[i].strip())
                    i += 1
                # Add the text for this entry
                transcript_lines.append(" ".join(text_lines))
                # Skip the blank line separating entries
                if i < len(lines) and lines[i].strip() == "":
                    i += 1
            else:
                i += 1

        original_text = " ".join(transcript_lines)
        print(f"  📄 Parsed {len(transcript_lines)} entries from '{original_language}' caption for {video_id[:10]}...")

        if not original_text.strip():
            print(f"  ⚠️  Parsed caption for {video_id} is empty after processing.")
            return ""

        # 5. Translate the original text to English (if not already English)
        # --- Use Google Cloud Translation API ---
        if original_language and original_language.lower().startswith('en'):
             print(f"  ✅ Transcript is already in English for {video_id[:10]}...")
             return original_text
        else:
             print(f"  🌐 Translating transcript from '{original_language}' to English for {video_id[:10]}...")
             try:
                 # --- Detect language first (robustness) ---
                 # Although we got the language from the API, detecting it ensures the text is valid
                 # and handles edge cases where the API might report incorrectly.
                 detection_result = translate_client.detect_language(original_text)
                 detected_lang = detection_result['language']
                 print(f"    🔍 Detected language: {detected_lang} (confidence: {detection_result.get('confidence', 'N/A')})")

                 # --- Translate if needed ---
                 if detected_lang.lower().startswith('en'):
                     print(f"    ✅ Detected text is already in English for {video_id[:10]}...")
                     return original_text
                 else:
                     # Translate the text to English
                     translation_result = translate_client.translate(
                         original_text,
                         target_language='en',
                         source_language=detected_lang # Specify source for better accuracy
                     )
                     translated_text = translation_result['translatedText']
                     print(f"    ✅ Transcript translated from '{detected_lang}' to English for {video_id[:10]}...")
                     return translated_text

             except Exception as trans_e:
                 print(f"    ⚠️  Translation failed for {video_id}: {trans_e}")
                 # Optionally, return the original text if translation fails
                 # print(f"    ℹ️  Returning original language text for {video_id[:10]}... (Length: {len(original_text)})")
                 # return original_text
                 return "" # Or return empty string if translation is critical


    except HttpError as http_err:
        error_details = http_err.error_details
        reason = error_details[0].get('reason') if error_details else ''
        if reason == 'captionNotAvailable':
            print(f"  ℹ️  Transcript disabled or unavailable for {video_id}.")
        else:
             print(f"  ⚠️  HTTP error fetching/downloading transcript for {video_id}: {http_err}")
    except Exception as e:
        # --- More specific error handling ---
        error_msg = str(e)
        print(f"  ⚠️  Could not fetch/download/parse transcript for {video_id} via API: {e}")
    return "" # Return empty string on any failure

async def main():
    """Main function to scrape both sale and rent listings."""
    print(f"--- Starting Scraper for {SITE_NAME} ---")
    
    # --- Scrape For Sale Listings ---
    sale_properties = await scrape_listings(BASE_URL_SALE, "for_sale", max_pages=300) # Scrape up to 300 pages for sale
    save_raw_data_to_gcs(sale_properties, "for_sale")
    
    # --- Scrape For Rent Listings ---
    rent_properties = await scrape_listings(BASE_URL_RENT, "for_rent", max_pages=300) # Scrape up to 300 pages for rent
    save_raw_data_to_gcs(rent_properties, "for_rent")
    
    # --- Placeholder for YouTube Scraping ---
    # This will be implemented separately using the official YouTube Data API v3
    # and the Google Cloud Translation API for transcript translation.
    # The function fetch_youtube_transcript_api above is part of this implementation.
    print("\n--- YouTube Scraping Placeholder ---")
    print("  ℹ️  YouTube scraping logic will be implemented separately.")
    print("  📌 Using fetch_youtube_transcript_api for transcript fetching & translation.")

    total_properties = len(sale_properties) + len(rent_properties)
    print(f"\n✅ Scraping completed for {SITE_NAME}. Total properties scraped: {total_properties}")

if __name__ == "__main__":
    asyncio.run(main())
