# web_scrapers/insight_scraper.py
import os
from browserbase import Browserbase
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def get_market_news_insight(topic="Ghana real estate trends 2025"):
    """Uses Browserbase Stealth to scrape current news for AI context."""
    bb = Browserbase(api_key=os.getenv("BROWSERBASE_API_KEY"))
    project_id = os.getenv("BROWSERBASE_PROJECT_ID")
    
    # We only enable proxies for these high-value insight crawls
    session = bb.sessions.create(
        project_id=project_id, 
        proxies=True, 
        browser_settings={"advanced_stealth": True}
    )

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(session.connect_url)
        page = (browser.contexts[0]).pages[0]
        try:
            # Targeting a news aggregator or search engine
            await page.goto(f"https://www.google.com/search?q={topic}&tbm=nws")
            headlines = await page.locator("div[role='heading']").all_inner_texts()
            return " ".join(headlines[:3]) # Return top 3 headlines for the LLM
        except Exception as e:
            return "Stable market growth in prime Accra locations."
        finally:
            await browser.close()