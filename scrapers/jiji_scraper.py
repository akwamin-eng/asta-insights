import os
import sys
import json
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, VirtualScrollConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from google.cloud import storage

load_dotenv()

# --- GCS Config ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager")
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

SITE_NAME = "jiji.com.gh"

# --- Extraction Schema for 2025 ---
JIJI_SCHEMA = {
    "name": "Jiji Listings",
    "baseSelector": "div.b-list-advert__gallery__item",
    "fields": [
        {"name": "title", "selector": "div.qa-advert-title", "type": "text"},
        {"name": "link", "selector": "a.b-list-advert-base", "type": "attribute", "attribute": "href"},
        {"name": "price_raw", "selector": "div.qa-advert-price", "type": "text"},
        {"name": "location", "selector": "span.b-list-advert__region__text", "type": "text"},
        {"name": "description", "selector": "div.b-list-advert-base__description-text", "type": "text"},
        {
            "name": "raw_features",
            "selector": "div.b-list-advert-base__attrs div.b-list-advert-base__item-attr",
            "type": "list",
            "fields": [{"name": "text", "selector": "", "type": "text"}]
        }
    ]
}

def parse_jiji_features(prop: Dict[str, Any]):
    """Extracts beds, baths, and area from the list of raw feature strings."""
    features = prop.get("raw_features", [])
    for f in features:
        text = f.get("text", "").lower()
        if "bdrm" in text or "bedroom" in text:
            match = re.search(r'(\d+)', text)
            if match: prop['bedrooms'] = int(match.group(1))
        elif "bath" in text:
            match = re.search(r'(\d+)', text)
            if match: prop['bathrooms'] = int(match.group(1))
        elif "sqm" in text:
            match = re.search(r'(\d+)', text)
            if match: prop['area_sqm'] = float(match.group(1))
    
    # Cleanup
    if "raw_features" in prop:
        del prop["raw_features"]
    return prop

async def main(scroll_count=20):
    targets = {
        "for_sale": "https://jiji.com.gh/houses-apartments-for-sale",
        "for_rent": "https://jiji.com.gh/houses-apartments-for-rent"
    }

    # Jiji requires a stronger browser config to pass Cloudflare Turnstile
    browser_cfg = BrowserConfig(
        headless=True,
        # Crawl4AI's internal stealth is usually enough, but we specify a common UA
        user_agent_mode="random", 
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for l_type, base_url in targets.items():
            print(f"🕵️ Jiji: Starting deep scroll for {l_type}...")
            
            # Use VirtualScrollConfig to handle Jiji's dynamic DOM replacement
            v_scroll = VirtualScrollConfig(
                container_selector="body", # Jiji usually scrolls the main body
                scroll_count=scroll_count,
                wait_after_scroll=1.5
            )

            config = CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(JIJI_SCHEMA),
                cache_mode=CacheMode.BYPASS,
                # scan_full_page=True, # Implicitly handled by VirtualScroll
                js_code=None # We rely on built-in scroll logic
            )
            
            # Note: VirtualScroll is a newer Crawl4AI feature. 
            # If your version doesn't support it yet, use scan_full_page=True.
            result = await crawler.arun(url=base_url, config=config)

            if result.success and result.extracted_content:
                items = json.loads(result.extracted_content)
                processed_items = []
                
                for item in items:
                    item = parse_jiji_features(item)
                    item.update({
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "listing_type": l_type,
                        "source": SITE_NAME,
                        "link": f"https://jiji.com.gh{item['link']}" if item.get('link') and not item['link'].startswith('http') else item.get('link')
                    })
                    processed_items.append(item)
                
                if processed_items:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    blob = bucket.blob(f"raw/{SITE_NAME}/{l_type}/{ts}.json")
                    blob.upload_from_string(json.dumps(processed_items, indent=2))
                    print(f"✅ Saved {len(processed_items)} Jiji items to GCS.")
            else:
                print(f"❌ Failed Jiji scrape: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
