import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy

# --- IMPORT FIX: Add root directory to path ---
sys.path.append(str(Path(__file__).parent.parent))
# ----------------------------------------------

from scrapers.stealth_config import get_stealth_browser_config, get_human_run_config, retry_with_backoff

load_dotenv()
bucket = storage.Client().bucket(os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager"))

SITE_NAME = "jiji.com.gh"
SCHEMA = {
    "name": "Jiji Stealth",
    "baseSelector": "div.b-list-advert__gallery__item",
    "fields": [
        {"name": "title", "selector": ".qa-advert-title", "type": "text"},
        {"name": "price", "selector": ".qa-advert-price", "type": "text"},
        {"name": "link", "selector": "a.b-list-advert-base", "type": "attribute", "attribute": "href"}
    ]
}

@retry_with_backoff(retries=3)
async def run_jiji_scrape(crawler, url, run_cfg):
    """Wraps the actual crawl in retry logic."""
    result = await crawler.arun(url=url, config=run_cfg)
    if not result.success:
        raise Exception(f"Crawl failed: {result.error_message}")
    return result

async def main():
    url = "https://jiji.com.gh/houses-apartments-for-sale"
    
    try:
        browser_cfg = get_stealth_browser_config()
        run_cfg = get_human_run_config(JsonCssExtractionStrategy(SCHEMA))
    except Exception as e:
        print(f"❌ Config Error: {e}")
        return

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        print(f"🛡️ Starting Stealth+Retry scrape for {SITE_NAME}...")
        try:
            result = await run_jiji_scrape(crawler, url, run_cfg)
        except Exception as e:
            print(f"💀 All retries failed: {e}")
            return

        if result and result.extracted_content:
            data = json.loads(result.extracted_content)
            print(f"✅ Extracted {len(data)} items.")
            
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_path = f"raw/property_listings/{SITE_NAME}/for_sale/{ts}.json"
            bucket.blob(blob_path).upload_from_string(json.dumps(data, indent=2))
            print(f"📂 Data uploaded to GCS: {blob_path}")
        else:
            print("⚠️ No content extracted.")

if __name__ == "__main__":
    asyncio.run(main())
