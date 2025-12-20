import os
import json
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from google.cloud import storage

load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data")
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

SITE_NAME = "tonaton.com"

# Using wildcard selectors because Tonaton uses dynamic classes like 'item--2G6S7'
TONATON_SCHEMA = {
    "name": "Tonaton Listings",
    "baseSelector": "li[class*='normal-item'], li[class*='top-item']",
    "fields": [
        {"name": "title", "selector": "h2[class*='title']", "type": "text"},
        {"name": "link", "selector": "a[class*='card-link']", "type": "attribute", "attribute": "href"},
        {"name": "price_raw", "selector": "div[class*='price']", "type": "text"},
        {"name": "location", "selector": "div[class*='location']", "type": "text"},
        {"name": "meta", "selector": "div[class*='description']", "type": "text"}
    ]
}

async def main(max_pages=20):
    targets = {
        "for_sale": "https://tonaton.com/en/ads/ghana/houses-for-sale",
        "for_rent": "https://tonaton.com/en/ads/ghana/houses-for-rent"
    }

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        for l_type, base_url in targets.items():
            all_results = []
            for p in range(1, max_pages + 1):
                print(f"🕵️ Tonaton: Scraping {l_type} page {p}...")
                url = f"{base_url}?page={p}"
                
                result = await crawler.arun(
                    url=url, 
                    config=CrawlerRunConfig(
                        extraction_strategy=JsonCssExtractionStrategy(TONATON_SCHEMA),
                        cache_mode=CacheMode.BYPASS,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                )

                if result.success and result.extracted_content:
                    items = json.loads(result.extracted_content)
                    if not items: break
                    
                    for item in items:
                        item.update({
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "listing_type": l_type,
                            "source": SITE_NAME,
                            "link": f"https://tonaton.com{item['link']}" if item.get('link') else None
                        })
                    all_results.extend(items)
                
                await asyncio.sleep(2)

            if all_results:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob = bucket.blob(f"raw/{SITE_NAME}/{l_type}/{ts}.json")
                blob.upload_from_string(json.dumps(all_results, indent=2))
                print(f"✅ Saved {len(all_results)} Tonaton items to GCS.")

if __name__ == "__main__":
    asyncio.run(main())
