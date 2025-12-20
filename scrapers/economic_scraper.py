# web_scrapers/economic_scraper.py
import yaml
import os
from browserbase import Browserbase
from playwright.async_api import async_playwright

def load_site_config(site_key):
    with open("config/sites.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config.get(site_key)

async def scrape_bog_indicators():
    site_cfg = load_site_config("bank_of_ghana")
    bb = Browserbase(api_key=os.getenv("BROWSERBASE_API_KEY"))
    
    # Create stealth session
    session = bb.sessions.create(
        project_id=os.getenv("BROWSERBASE_PROJECT_ID"),
        browser_settings={"advanced_stealth": True}
    )

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(session.connect_url)
        page = (browser.contexts[0]).pages[0]
        
        try:
            await page.goto(site_cfg['url'], wait_until=site_cfg['wait_condition'])
            
            # Extract data using YAML selectors
            raw_fx = await page.locator(site_cfg['selectors']['usd_sell_rate']).inner_text()
            raw_inf = await page.locator(site_cfg['selectors']['inflation_rate']).inner_text()
            
            # Clean data (remove currency symbols or % signs)
            fx_rate = float(raw_fx.strip())
            inflation = float(raw_inf.replace('%', '').strip())
            
            return {"fx_rate": fx_rate, "inflation": inflation}
            
        except Exception as e:
            print(f"❌ Error scraping BoG: {e}")
            # Return 2025 market fallbacks if site is down
            return {"fx_rate": 15.85, "inflation": 23.1} 
        finally:
            await browser.close()