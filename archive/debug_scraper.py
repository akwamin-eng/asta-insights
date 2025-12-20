import asyncio
import json
import os
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from dotenv import load_dotenv

load_dotenv()

async def debug_site(name, url, schema):
    print(f"\n--- Debugging {name} ---")
    print(f"Target: {url}")
    
    browser_cfg = BrowserConfig(headless=True, verbose=True)
    run_cfg = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema),
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)
        
        if not result.success:
            print(f"❌ Crawl Failed! Error: {result.error_message}")
            return

        print(f"✅ Crawl Successful (Status: {result.status_code})")
        
        # Check Content
        if result.extracted_content:
            data = json.loads(result.extracted_content)
            print(f"📦 Items Found: {len(data)}")
            if len(data) > 0:
                print(f"📝 Sample Data: {json.dumps(data[0], indent=2)[:200]}...")
            else:
                print("⚠️ Zero items extracted. The selectors might be outdated.")
                # Save HTML to see what happened
                with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
                    f.write(result.html)
                print(f"📂 Saved raw HTML to debug_{name}.html. Open this to check for bot blocks.")

# Test Schemas
MEQASA_SCHEMA = {"name": "Meqasa", "baseSelector": "div.col-xs-12.col-sm-12.col-md-5", "fields": [{"name": "t", "selector": "h2", "type": "text"}]}
TONATON_SCHEMA = {"name": "Tonaton", "baseSelector": "li[class*='item']", "fields": [{"name": "t", "selector": "h2", "type": "text"}]}

async def main():
    await debug_site("meqasa", "https://meqasa.com/houses-for-sale-in-ghana", MEQASA_SCHEMA)
    await debug_site("tonaton", "https://tonaton.com/en/ads/ghana/houses-for-sale", TONATON_SCHEMA)

if __name__ == "__main__":
    asyncio.run(main())
