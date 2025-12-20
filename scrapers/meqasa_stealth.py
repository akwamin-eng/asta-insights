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

# BROAD SELECTORS FOR DECEMBER 2025
SCHEMA = {
    "name": "Meqasa Universal",
    "baseSelector": "div[class*='prop'], .mqs-prop-dt-wrapper, .featured-prop-inner, article",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": ".h3, [class*='price'], .price", "type": "text"},
        {"name": "link", "selector": "a[href*='house'], a[href*='apartment']", "type": "attribute", "attribute": "href"}
    ]
}

async def main():
    url = "https://meqasa.com/houses-for-sale-in-ghana?w=1&p=1"
    browser_cfg = get_stealth_browser_config()

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(SCHEMA),
            cache_mode=CacheMode.BYPASS,
            # wait_for changed to a more generic element
            wait_for="h2", 
            delay_before_return_html=8.0 # Increased delay for proxy latency
        )
        
        print("🏡 Meqasa: Executing Universal 2025 Stealth Scrape...")
        result = await crawler.arun(url=url, config=config)
        
        if result.success and result.extracted_content:
            items = json.loads(result.extracted_content)
            # Filter valid items
            items = [i for i in items if i.get('title') and len(i['title']) > 5]
            
            if items:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_path = f"raw/property_listings/meqasa.com/for_sale/{ts}.json"
                bucket.blob(blob_path).upload_from_string(json.dumps(items, indent=2))
                print(f"✅ Saved {len(items)} items to {blob_path}")
            else:
                print("⚠️  No items extracted. Saving HTML for manual review...")
                with open("failed_meqasa.html", "w") as f: f.write(result.html)
        else:
            print(f"❌ Crawl Failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
