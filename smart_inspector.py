import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler

sys.path.append(str(Path(__file__).parent.parent))
from scrapers.stealth_config import get_stealth_browser_config, get_human_run_config

load_dotenv()

async def inspect(site_name, url):
    print(f"🔍 Inspecting {site_name} at {url}...")
    browser_cfg = get_stealth_browser_config()
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # We don't use a schema, just a raw crawl
        result = await crawler.arun(url=url)
        
        filename = f"inspect_{site_name}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result.html)
        
        print(f"✅ HTML saved to {filename}")
        print(f"📏 Content length: {len(result.html)} characters")
        if "captcha" in result.html.lower() or "verify you are human" in result.html.lower():
            print("⚠️ WARNING: Detected a CAPTCHA or Bot Block in the HTML!")

if __name__ == "__main__":
    asyncio.run(inspect("meqasa", "https://meqasa.com/houses-for-sale-in-ghana"))
    asyncio.run(inspect("tonaton", "https://tonaton.com/en/ads/ghana/houses-for-sale"))
