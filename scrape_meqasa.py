# scrape_meqasa.py
"""
Scraper for Meqasa.com using Crawl4AI.
Fetches property listings for sale and rent in Ghana.
Handles JavaScript pagination using Crawl4AI's features.
Saves raw data to GCS.
Integrates Google Cloud Translation API for non-English transcripts (if needed).
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
# Uses Application Default Credentials (ADC)
translate_client = translate.Client()
print("✅ Google Cloud Translation client built using ADC.")

# --- Site Configuration ---
SITE_NAME = "meqasa.com"
BASE_URL_SALE = "https://meqasa.com/houses-for-sale-in-ghana"
BASE_URL_RENT = "https://meqasa.com/houses-for-rent-in-accra" # Accra-specific for rent?

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

# --- Extraction Strategy Schema for Meqasa.com ---
# Define a schema to extract property listing data using JsonCssExtractionStrategy
# Based on the HTML structure observed on 2025-10-13 for https://meqasa.com/houses-for-sale-in-ghana
# Key classes/structure from the snippet:
# <div class="col-xs-12 col-sm-12 col-md-5"> (Outer container)
#   <div class="mqs-prop-dt-wrapper"> (Inner container)
#     <h2><a href="/house-for-sale-at-East-Legon-450748?y=1199836797">3 bedroom house for sale in East Legon</a></h2>
#     <p class="h3"><span class="h3">Price</span>GH₵14,640,972 <span></span></p>
#     <p>Luxurious 3-Bedroom Home for Sale in East Legon, Accra! .... <a href="...">Read more</a></p> (Description)
#     <ul class="prop-features">
#       <li class="bed"><span>3</span></li>
#       <li class="shower"><span>3</span></li>
#       <li title="Garages" class="garage"><span>7</span></li>
#       ...
#     </ul>
PROPERTY_SCHEMA_MEQASA = {
    "name": "Meqasa.com Ghana Listings",
    "baseSelector": "div.row.mqs-featured-prop-inner-wrap.clickable", # Updated container selector
    "fields": [
        {
            "name": "title",
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper h2 a", # Updated selector
            "type": "text"
        },
        {
            "name": "link",
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper h2 a", # Updated selector
            "type": "attribute",
            "attribute": "href"
        },
        {
            "name": "price_text", # Raw price text including currency symbol
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper p.h3", # Updated selector
            "type": "text"
        },
        {
            "name": "description_snippet", # Short description snippet
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper > p:nth-of-type(2)", # Updated selector (2nd <p> child)
            "type": "text"
        },
        {
            "name": "bedrooms_text", # Raw text content of the bed span
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper ul.prop-features li.bed span", # Updated selector
            "type": "text"
        },
        {
            "name": "bathrooms_text", # Raw text content of the shower span
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper ul.prop-features li.shower span", # Updated selector
            "type": "text"
        },
        {
            "name": "garages_text", # Raw text content of the garage span
            "selector": "div.col-xs-12.col-sm-12.col-md-5 div.mqs-prop-dt-wrapper ul.prop-features li.garage span", # Updated selector
            "type": "text"
        }
        # Add more fields if needed (e.g., image URL from img-carousel if available in the snippet)
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

async def scrape_listings_meqasa(url: str, listing_type: str, max_pages: int = 300) -> List[Dict[str, Any]]:
    """
    Scrapes property listings from a given Meqasa URL (sale or rent) for a specified number of pages.
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
                # Use JsonCssExtractionStrategy with the defined schema for Meqasa
                extraction_strategy = JsonCssExtractionStrategy(PROPERTY_SCHEMA_MEQASA)
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
                                # Add metadata like page number, scrape time, source
                                for prop in extracted_data:
                                    # Post-process raw text fields to extract numerical values
                                    # Price
                                    price_text = prop.get("price_text", "")
                                    if price_text:
                                        # Extract numeric part (remove currency symbols, commas)
                                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                                        if price_match:
                                            try:
                                                prop['price_numeric'] = float(price_match.group(0))
                                            except ValueError:
                                                prop['price_numeric'] = None
                                        else:
                                            prop['price_numeric'] = None
                                    # Bedrooms
                                    bedrooms_text = prop.get("bedrooms_text", "")
                                    if bedrooms_text and bedrooms_text.isdigit():
                                        prop['bedrooms'] = int(bedrooms_text)
                                    # Bathrooms/Shower
                                    bathrooms_text = prop.get("bathrooms_text", "")
                                    if bathrooms_text and bathrooms_text.isdigit():
                                        prop['bathrooms'] = int(bathrooms_text)
                                    # Garages
                                    garages_text = prop.get("garages_text", "")
                                    if garages_text and garages_text.isdigit():
                                        prop['garages'] = int(garages_text)
                                    
                                    # Add common metadata
                                    prop['scraped_at'] = datetime.now(timezone.utc).isoformat()
                                    prop['listing_type'] = listing_type
                                    prop['source_site'] = SITE_NAME
                                    prop['page_number'] = current_page
                                
                                all_properties.extend(extracted_data)
                            else:
                                print(f"    ⚠️  Extracted content is not a list on page {current_page}: {type(extracted_data)}")
                        except json.JSONDecodeError as je:
                            print(f"    ⚠️  JSON decode error for extracted content on page {current_page}: {je}")
                            print(f"    Raw extracted content snippet: {result.extracted_content[:200]}...")
                    else:
                        print(f"    ℹ️  No extracted content found on page {current_page}.")
                    
                    # --- Find Next Page URL ---
                    # This is highly dependent on the site's structure.
                    # Inspect the actual HTML to find the correct selector for the "Next" page link.
                    # For Meqasa, it might be a link with text 'Next' or an arrow icon within a pagination div.
                    # You'll need to inspect the actual HTML to find the correct selector.
                    # Example (hypothetical, needs verification):
                    # next_page_element = result.html.find('a', string='Next')
                    # if next_page_element and next_page_element.get('href'):
                    #     next_page_url = next_page_element.get('href')
                    #     # Make sure it's a full URL or prepend the base URL
                    #     if not next_page_url.startswith('http'):
                    #         from urllib.parse import urljoin
                    #         next_page_url = urljoin(url, next_page_url)
                    # else:
                    #     next_page_url = None
                    
                    # --- TEMPORARY: Stop after one page for testing ---
                    print(f"    ⏸️  Stopping after page {current_page} for testing. Next page logic needs implementation.")
                    next_page_url = None # Remove this line when implementing next page logic
                    
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

# --- THIS IS THE ENTRY POINT FOR MEQASA SCRAPER ---
async def main():
    """Main function to scrape both sale and rent listings from Meqasa."""
    print(f"--- Starting Scraper for {SITE_NAME} ---")
    
    # --- Scrape For Sale Listings ---
    sale_properties = await scrape_listings_meqasa(BASE_URL_SALE, "for_sale", max_pages=300) # Scrape up to 300 pages for sale
    save_raw_data_to_gcs(sale_properties, "for_sale")
    
    # --- Scrape For Rent Listings ---
    rent_properties = await scrape_listings_meqasa(BASE_URL_RENT, "for_rent", max_pages=300) # Scrape up to 300 pages for rent
    save_raw_data_to_gcs(rent_properties, "for_rent")
    
    total_properties = len(sale_properties) + len(rent_properties)
    print(f"\n✅ Scraping completed for {SITE_NAME}. Total properties scraped: {total_properties}")

if __name__ == "__main__":
    asyncio.run(main())
