import asyncio
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.cloud import storage
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, VirtualScrollConfig
from scrapers.stealth_config import get_stealth_browser_config, get_human_run_config

load_dotenv()
bucket = storage.Client().bucket(os.getenv("GCS_BUCKET_NAME"))

SITE_NAME = "jiji.com.gh"
SCHEMA = {
    "name": "Jiji Stealth Extraction",
    "baseSelector": "div.b-list-advert__gallery__item",
    "fields": [
        {"name": "title", "selector": ".qa-advert-title", "type": "text"},
        {"name": "price", "selector": ".qa-advert-price", "type": "text"},
        {"name": "link", "selector": "a.b-list-advert-base", "type": "attribute", "attribute": "href"},
        {"name": "location", "selector": ".b-list-advert__region__text", "type": "text"}
    ]
}

async def main():
    url = "https://jiji.com.gh/houses-apartments-for-sale"
    
    # Setup stealth browser with proxies
    browser_cfg = get_stealth_browser_config()
    
    # Configure Virtual Scroll for Jiji's infinite list
    run_cfg = get_human_run_config(JsonCssExtractionStrategy(SCHEMA))
    # Note: VirtualScroll is highly effective for Jiji's dynamic DOM replacement
    run_cfg.virtual_scroll = VirtualScrollConfig(
        scroll_count=10, 
        wait_after_scroll=1.5
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        print(f"🚀 Scraping {SITE_NAME} using Stealth + Proxies...")
        result = await crawler.arun(url=url, config=run_cfg)

        if result.success and result.extracted_content:
            data = json.loads(result.extracted_content)
            print(f"✅ Found {len(data)} items.")
            
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_path = f"raw/property_listings/{SITE_NAME}/for_sale/{ts}.json"
            bucket.blob(blob_path).upload_from_string(
                json.dumps(data, indent=2), content_type='application/json'
            )
            print(f"📂 Data saved to: {blob_path}")
        else:
            print(f"❌ Scrape failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
