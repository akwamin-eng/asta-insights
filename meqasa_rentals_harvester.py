import asyncio
import json
import os
import random
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# --- CONFIGURATION ---
# TARGETING RENTALS NOW
BASE_URL = "https://meqasa.com/apartments-for-rent-in-ghana?w=1&p="
START_PAGE = 1
MAX_PAGES = 50  # Start with 50 pages of rentals
OUTPUT_FILE = "meqasa_rentals_dump.json"

SCHEMA = {
    "name": "Meqasa Rental Card",
    "baseSelector": "div.mqs-prop-dt-wrapper", 
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": "p.h3", "type": "text"},
        {"name": "location", "selector": "h2", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "beds", "selector": "li:has(i.fa-bed) span", "type": "text"}
    ]
}

async def scrape_rentals():
    seen_ids = set()
    master_list = []
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36"}
    )

    print(f"🚀 Starting Rental Scrape (Pages {START_PAGE}-{MAX_PAGES})...")
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page_num in range(START_PAGE, MAX_PAGES + 1):
            url = f"{BASE_URL}{page_num}"
            await asyncio.sleep(random.uniform(1.5, 3.0)) 
            
            try:
                run_config = CrawlerRunConfig(
                    extraction_strategy=JsonCssExtractionStrategy(SCHEMA),
                    cache_mode=CacheMode.BYPASS,
                    wait_for="div.mqs-prop-dt-wrapper",
                    delay_before_return_html=2.0
                )
                
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success:
                    raw_items = json.loads(result.extracted_content)
                    
                    for item in raw_items:
                        full_url = item.get('url', '')
                        if not full_url.startswith("http"): full_url = f"https://meqasa.com{full_url}"
                        
                        # CLEAN URL ID (Remove the ?y=... garbage immediately)
                        clean_id_part = full_url.split('?')[0].split('/')[-1]
                        unique_id = f"meqasa_rent_{clean_id_part}"
                        
                        if unique_id in seen_ids: continue
                        seen_ids.add(unique_id)
                        
                        master_list.append({
                            "id": unique_id,
                            "source": "Meqasa",
                            "title": item.get('title', 'Unknown').strip(),
                            "price": item.get('price', '0').strip(),
                            "location": item.get('title', 'Unknown').strip(),
                            "url": full_url,
                            "beds": item.get('beds', '0'),
                            "type": "Rent", # Explicitly tag as Rent
                            "scraped_at": datetime.now().isoformat()
                        })
                    
                    print(f"✅ Page {page_num}: Added {len(raw_items)} rentals. (Total: {len(master_list)})")
            except Exception as e:
                print(f"⚠️ Error Page {page_num}: {e}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(master_list, f, indent=2)
    print(f"💾 Saved {len(master_list)} rentals to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scrape_rentals())
