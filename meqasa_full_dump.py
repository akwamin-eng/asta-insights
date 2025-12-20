import asyncio
import json
import os
import random
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# --- CONFIGURATION ---
BASE_URL = "https://meqasa.com/houses-for-sale-in-ghana?w=1&p="
START_PAGE = 1
MAX_PAGES = 551  # Set to 551 for the full dump
OUTPUT_FILE = "meqasa_master_dump.json"

# --- SCHEMA ---
SCHEMA = {
    "name": "Meqasa Card Extraction",
    "baseSelector": "div.mqs-prop-dt-wrapper", 
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": "p.h3", "type": "text"},
        {"name": "location", "selector": "h2", "type": "text"}, # Fallback if location isn't separate
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "beds", "selector": "li:has(i.fa-bed) span", "type": "text"},
        {"name": "showers", "selector": "li:has(i.fa-shower) span", "type": "text"},
        {"name": "garages", "selector": "li:has(i.fa-car) span", "type": "text"},
        {"name": "area", "selector": "li:has(i.fa-ruler-combined) span", "type": "text"}
    ]
}

async def scrape_full_catalog():
    # 1. SETUP STATE
    # We use a set to track URLs we have already seen.
    # This automatically filters out the "Featured" properties that repeat on every page.
    seen_urls = set()
    master_list = []
    
    # Load existing progress if restarting
    if os.path.exists(OUTPUT_FILE):
        print(f"🔄 Found existing {OUTPUT_FILE}, loading to prevent duplicates...")
        try:
            with open(OUTPUT_FILE, 'r') as f:
                existing_data = json.load(f)
                for item in existing_data:
                    seen_urls.add(item['url'])
                    master_list.append(item)
            print(f"   Loaded {len(master_list)} existing records.")
        except:
            print("   ⚠️ Could not read existing file, starting fresh.")

    # 2. BROWSER CONFIG
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    print(f"🚀 Starting Full Scrape: Pages {START_PAGE} to {MAX_PAGES}")
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page_num in range(START_PAGE, MAX_PAGES + 1):
            url = f"{BASE_URL}{page_num}"
            
            # Rate Limiting: Sleep randomly between 2 and 5 seconds to be polite
            await asyncio.sleep(random.uniform(2.0, 5.0))
            
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
                    new_items_count = 0
                    
                    for item in raw_items:
                        # cleanup URL
                        full_url = item.get('url', '')
                        if full_url and not full_url.startswith("http"):
                            full_url = f"https://meqasa.com{full_url}"
                        
                        # DEDUPLICATION CHECK
                        if full_url in seen_urls:
                            continue # Skip this duplicate
                        
                        # Add new item
                        seen_urls.add(full_url)
                        
                        clean_item = {
                            "source": "Meqasa",
                            "id": f"meqasa_{full_url.split('/')[-1]}", # Generate Stable ID
                            "title": item.get('title', 'Unknown').strip(),
                            "price": item.get('price', '0').strip(),
                            "location": item.get('title', 'Unknown').strip(), # Needs refinement later
                            "url": full_url,
                            "beds": item.get('beds', '0'),
                            "showers": item.get('showers', '0'),
                            "garages": item.get('garages', '0'),
                            "area": item.get('area', '0'),
                            "scraped_at": datetime.now().isoformat()
                        }
                        
                        master_list.append(clean_item)
                        new_items_count += 1
                    
                    print(f"✅ Page {page_num}: Found {len(raw_items)} raw -> Added {new_items_count} UNIQUE items. (Total: {len(master_list)})")
                    
                    # 3. INCREMENTAL SAVE (Safety Net)
                    if page_num % 5 == 0: # Save every 5 pages
                        print(f"💾 Checkpoint: Saving {len(master_list)} items to disk...")
                        with open(OUTPUT_FILE, "w") as f:
                            json.dump(master_list, f, indent=2)
                            
                else:
                    print(f"❌ Page {page_num} failed: {result.error_message}")
            
            except Exception as e:
                print(f"⚠️ Critical Error on Page {page_num}: {e}")
                # We continue to the next page instead of crashing
                continue

    # Final Save
    print("\n" + "="*50)
    print(f"🎉 DONE! Scraped {MAX_PAGES} pages.")
    print(f"📊 Total Unique Properties: {len(master_list)}")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(master_list, f, indent=2)
    print(f"💾 Final data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scrape_full_catalog())
