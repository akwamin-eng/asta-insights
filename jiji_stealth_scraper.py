import asyncio
import json
import os
from datetime import datetime
# from dotenv import load_dotenv # Uncomment if you have your .env file ready
# from google.cloud import storage # Uncomment if you have auth set up
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# --- MOCK GCS FOR TESTING (Replace with your real GCS code) ---
class MockBucket:
    def blob(self, path): return self
    def upload_from_string(self, data, content_type):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(data)

bucket = MockBucket() 
SITE_NAME = "jiji.com.gh"

# --- SCHEMA ---
SCHEMA = {
    "name": "Jiji Stealth Extraction",
    "baseSelector": "div.b-list-advert__gallery__item",
    "fields": [
        {"name": "title", "selector": ".qa-advert-title", "type": "text"},
        {"name": "price", "selector": ".qa-advert-price", "type": "text"},
        {"name": "link", "selector": "a.b-list-advert-base", "type": "attribute", "attribute": "href"},
        {"name": "location", "selector": ".b-list-advert__region__text", "type": "text"}
    ]
}

async def main():
    url = "https://jiji.com.gh/houses-apartments-for-sale"
    
    # 1. CONFIGURE PERSISTENT BROWSER
    # This creates a folder 'jiji_browser_profile' where cookies/auth are saved.
    browser_cfg = BrowserConfig(
        headless=False,  # <--- MUST BE FALSE TO SOLVE CAPTCHA MANUALLY
        verbose=True,
        user_data_dir="./jiji_browser_profile", # <--- SAVES YOUR SESSION
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    # 2. RUN CONFIG
    run_cfg = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(SCHEMA),
        cache_mode=CacheMode.BYPASS,
        # Scroll keeps the session active and loads more data
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="css:div.b-list-advert__gallery__item",
        delay_before_return_html=5.0 
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        print(f"🚀 Scraping {SITE_NAME}...")
        print("👀 Browser will open. If you see Cloudflare, SOLVE IT MANUALLY.")
        
        # arun() opens the browser. 
        # Since we use a persistent profile, once you solve it, the cookie is saved.
        result = await crawler.arun(url=url, config=run_cfg)

        if result.success:
            # The extraction strategy might return a JSON string or dict depending on version
            try:
                data = json.loads(result.extracted_content)
            except:
                data = result.extracted_content

            if data:
                print(f"✅ Found {len(data)} items.")
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Saving locally for now to test
                blob_path = f"raw_property_listings_{ts}.json"
                
                with open(blob_path, "w") as f:
                    json.dump(data, f, indent=2)
                    
                print(f"📂 Data saved to: {blob_path}")
            else:
                print("⚠️  Page loaded, but no items found (Selectors might need tuning).")
        else:
            print(f"❌ Scrape failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
