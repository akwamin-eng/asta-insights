import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
# Ensure you have the latest crawl4ai installed
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# --- SETUP ---
load_dotenv()
# If you don't have GCS creds locally, this will fail. 
# For now, we save locally to ensure it works first.
USE_GCS = os.getenv("GCS_BUCKET_NAME") is not None
if USE_GCS:
    bucket = storage.Client().bucket(os.getenv("GCS_BUCKET_NAME"))

# --- MEQASA SCHEMA ---
# This schema targets the specific cards on meqasa.com
SCHEMA = {
    "name": "Meqasa Listings",
    "baseSelector": "div.mqs-prop-dt-wrapper", 
    "fields": [
        {
            "name": "title", 
            "selector": "h2", 
            "type": "text"
        },
        {
            "name": "price", 
            "selector": "p.h3", 
            "type": "text"
        },
        {
            "name": "location",
            "selector": "h2", # Meqasa often puts location in the H2 or a span nearby
            "type": "text" 
        },
        {
            "name": "url", 
            "selector": "a", 
            "type": "attribute", 
            "attribute": "href"
        },
        {
            "name": "beds",
            "selector": "li:has(i.fa-bed) span",
            "type": "text"
        }
    ]
}

async def scrape_meqasa():
    # We will scrape pages 1 to 3
    base_url = "https://meqasa.com/houses-for-sale-in-ghana?w=1&p="
    all_properties = []

    # Basic Browser Config (Headless is usually fine for Meqasa)
    browser_config = BrowserConfig(
        headless=True,
        verbose=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page_num in range(1, 4): # Pages 1, 2, 3
            url = f"{base_url}{page_num}"
            print(f"🌍 Scraping Meqasa Page {page_num}...")

            run_config = CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(SCHEMA),
                cache_mode=CacheMode.BYPASS,
                wait_for="div.mqs-prop-dt-wrapper", # Wait for the cards to load
                delay_before_return_html=3.0 
            )

            result = await crawler.arun(url=url, config=run_config)

            if result.success:
                data = json.loads(result.extracted_content)
                print(f"   ✅ Found {len(data)} items on page {page_num}")
                
                # Normalize Data immediately
                for item in data:
                    if not item.get('title'): continue
                    
                    # Fix relative URLs
                    full_url = item['url']
                    if full_url and not full_url.startswith("http"):
                        full_url = f"https://meqasa.com{full_url}"

                    all_properties.append({
                        "source": "Meqasa",
                        "title": item.get('title', 'Unknown'),
                        "price": item.get('price', '0'),
                        "location": item.get('title', 'Unknown'), # Meqasa titles are usually "4 Bedroom House for sale in Osu"
                        "url": full_url,
                        "beds": item.get('beds', '0')
                    })
            else:
                print(f"   ❌ Failed to scrape page {page_num}: {result.error_message}")
                
            # Polite pause between pages
            await asyncio.sleep(2)

    # --- SAVE RESULTS ---
    output_filename = f"meqasa_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 1. Save Locally
    with open(output_filename, "w") as f:
        json.dump(all_properties, f, indent=2)
    print(f"\n💾 Saved {len(all_properties)} properties locally to {output_filename}")

    # 2. Upload to GCS (if configured)
    if USE_GCS:
        blob_path = f"raw/property_listings/meqasa.com/for_sale/{os.path.basename(output_filename)}"
        bucket.blob(blob_path).upload_from_filename(output_filename)
        print(f"☁️  Uploaded to GCS: {blob_path}")

if __name__ == "__main__":
    asyncio.run(scrape_meqasa())
