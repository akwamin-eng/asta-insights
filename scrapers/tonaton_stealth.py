import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode

sys.path.append(str(Path(__file__).parent.parent))
from scrapers.stealth_config import get_stealth_browser_config, retry_with_backoff

load_dotenv()
bucket = storage.Client().bucket(os.getenv("GCS_BUCKET_NAME"))

SCHEMA = {
    "name": "Tonaton Broad 2025",
    "baseSelector": "li[data-testid*='listing'], article, div[class*='item']",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": "[data-testid*='price'], [class*='price']", "type": "text"},
        {"name": "link", "selector": "a[href*='ads']", "type": "attribute", "attribute": "href"}
    ]
}

async def main():
    url = "https://tonaton.com/en/ads/ghana/houses-for-sale"
    browser_cfg = get_stealth_browser_config()
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(SCHEMA),
            cache_mode=CacheMode.BYPASS,
            wait_for="h2", 
            delay_before_return_html=8.0
        )
        
        print("👻 Tonaton: Executing Broad Stealth Scrape...")
        result = await crawler.arun(url=url, config=config)
        
        if result.success and result.extracted_content:
            items = json.loads(result.extracted_content)
            items = [i for i in items if i.get('title')]
            if items:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_path = f"raw/property_listings/tonaton.com/for_sale/{ts}.json"
                bucket.blob(blob_path).upload_from_string(json.dumps(items, indent=2))
                print(f"✅ Saved {len(items)} items to {blob_path}")
            else:
                print("⚠️  No items found. Saving HTML...")
                with open("failed_tonaton.html", "w") as f: f.write(result.html)

if __name__ == "__main__":
    asyncio.run(main())
