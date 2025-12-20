import os
import sys
import json
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from google.cloud import storage

load_dotenv()

# --- GCS Config ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data")
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

SITE_NAME = "meqasa.com"

# --- Extraction Schema ---
MEQASA_SCHEMA = {
    "name": "Meqasa Listings",
    "baseSelector": "div.col-xs-12.col-sm-12.col-md-5",
    "fields": [
        {"name": "title", "selector": "h2 a", "type": "text"},
        {"name": "link", "selector": "h2 a", "type": "attribute", "attribute": "href"},
        {"name": "price_raw", "selector": "p.h3", "type": "text"},
        {"name": "description", "selector": "p:nth-of-type(2)", "type": "text"},
        {"name": "bed", "selector": "li.bed span", "type": "text"},
        {"name": "bath", "selector": "li.shower span", "type": "text"},
        {"name": "garage", "selector": "li.garage span", "type": "text"}
    ]
}

def clean_price(raw_price: str) -> Dict[str, Any]:
    """Extracts numeric value and currency from strings like 'GH₵14,640,972' or '$300,000'."""
    if not raw_price: return {"value": None, "currency": None}
    raw_price = raw_price.replace("Price", "").strip()
    currency = "USD" if "$" in raw_price else "GHS"
    nums = re.sub(r'[^\d.]', '', raw_price)
    try:
        return {"value": float(nums), "currency": currency}
    except:
        return {"value": None, "currency": currency}

async def scrape_meqasa_page(crawler, url, page_num, listing_type):
    config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(MEQASA_SCHEMA),
        cache_mode=CacheMode.BYPASS,
        session_id="meqasa_session"
    )
    result = await crawler.arun(url=f"{url}?w=1&p={page_num}", config=config)
    
    if not result.success or not result.extracted_content:
        return []

    items = json.loads(result.extracted_content)
    for item in items:
        price_data = clean_price(item.get("price_raw", ""))
        item.update({
            "price_value": price_data["value"],
            "currency": price_data["currency"],
            "page": page_num,
            "listing_type": listing_type,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": SITE_NAME
        })
        if item.get("link") and not item["link"].startswith("http"):
            item["link"] = f"https://meqasa.com{item['link']}"
            
    return items

async def main(max_pages=50):
    targets = {
        "for_sale": "https://meqasa.com/houses-for-sale-in-ghana",
        "for_rent": "https://meqasa.com/houses-for-rent-in-ghana"
    }
    
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        for l_type, base_url in targets.items():
            all_results = []
            for p in range(1, max_pages + 1):
                print(f"🕵️ Meqasa: Scraping {l_type} page {p}...")
                page_data = await scrape_meqasa_page(crawler, base_url, p, l_type)
                if not page_data: break
                all_results.extend(page_data)
                await asyncio.sleep(1) # Rate limit protection

            if all_results:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob = bucket.blob(f"raw/{SITE_NAME}/{l_type}/{ts}.json")
                blob.upload_from_string(json.dumps(all_results, indent=2))
                print(f"✅ Saved {len(all_results)} {l_type} items to GCS.")

if __name__ == "__main__":
    asyncio.run(main())
