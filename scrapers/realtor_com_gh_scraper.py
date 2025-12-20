# scrapers/realtor_com_gh_scraper.py
"""
One-time scraper for Realtor.com Ghana International Listings.
Fetches data for all 7 pages and saves raw data to GCS.
Integrates Crawl4AI for robust scraping.
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

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# --- GCS Configuration ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager")
storage_client = storage.Client()
gcs_bucket = storage_client.bucket(GCS_BUCKET_NAME)

# --- Realtor.com Ghana Configuration ---
SITE_NAME = "realtor.com"
BASE_URL = "https://www.realtor.com/international/gh/"

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

# --- Extraction Strategy Schema for Realtor.com Ghana ---
# Define a schema to extract property listing data using JsonCssExtractionStrategy
# Based on the HTML structure observed on 2025-10-13 for https://www.realtor.com/international/gh/
# IMPORTANT: These selectors are based on the provided HTML snippet and might need adjustment
# after inspecting the live site's actual structure.
PROPERTY_SCHEMA_REALTOR_COM = {
    "name": "Realtor.com Ghana Listings",
    "baseSelector": "div[data-testid='standard-listing-card']", # More robust selector using data-testid
    "fields": [
        {
            "name": "title", # Using address as title for now
            "selector": "div.address",
            "type": "text"
        },
        {
            "name": "link",
            "selector": "a", # The <a> tag is the direct child of baseSelector
            "type": "attribute",
            "attribute": "href"
        },
        {
            "name": "price",
            "selector": "div.price div.displayConsumerPrice", # Target the consumer price display
            "type": "text"
        },
        {
            "name": "address",
            "selector": "div.address",
            "type": "text"
        },
        # --- Extracting Features (Beds, Baths, Area) ---
        # Since features aren't uniquely classed, we extract all feature items
        # and will parse them in post-processing within the scraper script.
        {
            "name": "raw_features",
            "selector": "div.features div.feature-item",
            "type": "list", # Get a list of all feature-item divs
            "fields": [
                {"name": "text", "selector": "", "type": "text"} # Get the text content of each feature-item
            ]
        }
        # Add more fields if needed (e.g., image URL from img-carousel)
    ]
}

def save_raw_data_to_gcs(data: List[Dict[str, Any]], listing_type: str = "realtor_com_gh"):
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

async def scrape_realtor_com_gh(base_url: str, max_pages: int = 7) -> List[Dict[str, Any]]:
    """
    Scrapes property listings from Realtor.com Ghana International section for a specified number of pages.
    Returns a list of property dictionaries.
    """
    print(f"  🕷️  Scraping {SITE_NAME} listings from {base_url[:50]}...")
    
    all_properties = []
    current_page = 1

    # Use a single browser instance for efficiency across pages
    async with AsyncWebCrawler(config=DEFAULT_BROWSER_CONFIG) as crawler:
        while current_page <= max_pages:
            # Construct the URL for the current page
            # Realtor.com Ghana uses pg-N for pagination
            if current_page == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}pg-{current_page}"
            
            print(f"    📄 Page {current_page}/{max_pages}: {page_url[:50]}...")
            
            try:
                # --- Configure CrawlerRunConfig for this page ---
                # Use JsonCssExtractionStrategy with the defined schema for Realtor.com
                extraction_strategy = JsonCssExtractionStrategy(PROPERTY_SCHEMA_REALTOR_COM)
                config = DEFAULT_CRAWLER_CONFIG.clone(extraction_strategy=extraction_strategy)
                
                # --- Run the crawl ---
                result = await crawler.arun(url=page_url, config=config)
                
                if result.success:
                    print(f"    ✅ Page {current_page} scraped successfully.")
                    
                    # --- Process Extracted Content ---
                    if result.extracted_content:
                        try:
                            extracted_data = json.loads(result.extracted_content)
                            if isinstance(extracted_data, list):
                                print(f"    📦 Found {len(extracted_data)} properties on page {current_page}.")
                                # Add metadata like page number, scrape time, source
                                for prop in extracted_data:
                                    prop['scraped_at'] = datetime.now(timezone.utc).isoformat()
                                    prop['listing_type'] = "realtor_com_gh"
                                    prop['source_site'] = SITE_NAME
                                    prop['page_number'] = current_page
                                    # Post-process raw_features to extract beds, baths, area if possible
                                    raw_features = prop.get("raw_features", [])
                                    if raw_features:
                                        for feature_item in raw_features:
                                            feature_text = feature_item.get("text", "").lower()
                                            if "bed" in feature_text:
                                                # Extract number before 'bed'
                                                bed_match = re.search(r'(\d+)\s*bed', feature_text)
                                                if bed_match:
                                                    prop['bedrooms'] = int(bed_match.group(1))
                                            elif "bath" in feature_text:
                                                # Extract number before 'bath'
                                                bath_match = re.search(r'(\d+)\s*bath', feature_text)
                                                if bath_match:
                                                    prop['bathrooms'] = int(bath_match.group(1))
                                            elif "sqm" in feature_text or "square meter" in feature_text:
                                                # Extract number before 'sqm' or 'square meter'
                                                area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sqm|square meter)', feature_text)
                                                if area_match:
                                                    prop['area_sqm'] = float(area_match.group(1))
                                            # Add more feature parsing logic if needed (e.g., acres, hectares)
                                        
                                        # Remove raw_features after parsing
                                        del prop['raw_features']
                                    
                                all_properties.extend(extracted_data)
                            else:
                                print(f"    ⚠️  Extracted content is not a list on page {current_page}: {type(extracted_data)}")
                        except json.JSONDecodeError as je:
                            print(f"    ⚠️  JSON decode error for extracted content on page {current_page}: {je}")
                            print(f"    Raw extracted content snippet: {result.extracted_content[:200]}...")
                    else:
                        print(f"    ℹ️  No extracted content found on page {current_page}.")
                    
                else:
                    print(f"    ❌ Failed to scrape page {current_page}: {result.error_message}")
                    # Stop scraping if a page fails
                    break
                    
            except Exception as e:
                print(f"    💥 Exception scraping page {current_page}: {e}")
                # Stop scraping if an exception occurs
                break
                
            # Increment page counter
            current_page += 1
            
            # Optional: Small delay between pages to be respectful
            if current_page <= max_pages:
                delay = 2.0 # seconds
                print(f"    ⏱️  Sleeping for {delay} seconds before next page...")
                await asyncio.sleep(delay)
                
    print(f"  📊 Total properties scraped for {SITE_NAME}: {len(all_properties)}")
    return all_properties

async def main():
    """Main function to scrape Realtor.com Ghana listings."""
    print(f"--- Starting One-Time Scraper for {SITE_NAME} ---")
    
    # --- Scrape Realtor.com Ghana Listings ---
    realtor_properties = await scrape_realtor_com_gh(BASE_URL, max_pages=7) # Scrape all 7 pages
    save_raw_data_to_gcs(realtor_properties, "realtor_com_gh")
    
    print(f"\n✅ One-time scraping completed for {SITE_NAME}. Total properties scraped: {len(realtor_properties)}")

if __name__ == "__main__":
    asyncio.run(main())
