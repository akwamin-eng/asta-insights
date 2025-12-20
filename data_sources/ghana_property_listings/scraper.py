# scrape_ghana_real_estate.py
import asyncio
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup
import time
import re

async def scrape_with_playwright(url, selector):
    """Scrape using Playwright (for JS-heavy sites)."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=10000)
            await page.wait_for_selector(selector, timeout=10000)
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print(f"⚠️ Playwright failed for {url}: {e}")
        return None

def scrape_with_requests(url):
    """Fallback: scrape with requests + BeautifulSoup."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AstaBot/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"⚠️ Requests failed for {url}: {e}")
        return None

def parse_meqasa_listings(html):
    """Parse Meqasa listings from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    for card in soup.select('div[data-testid="listing-card"]'):
        try:
            price_elem = card.select_one('p[class*="price"]')
            if not price_elem:
                continue
            price = int(re.sub(r'[^\d]', '', price_elem.text))
            title = card.select_one('h3').text.strip() if card.select_one('h3') else "No title"
            listings.append({"source": "meqasa", "title": title, "price": price})
        except Exception:
            continue
    return listings

def parse_tonaton_listings(html):
    """Parse Tonaton listings from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    for item in soup.select('div[class*="card"]'):
        try:
            price_elem = item.select_one('.price')
            if not price_elem:
                continue
            price = int(re.sub(r'[^\d]', '', price_elem.text))
            title = item.select_one('h3 a').text.strip() if item.select_one('h3 a') else "No title"
            listings.append({"source": "tonaton", "title": title, "price": price})
        except Exception:
            continue
    return listings

async def scrape_all():
    listings = []

    # Meqasa (try Playwright first, then requests)
    meqasa_url = "https://meqasa.com/houses-for-rent-in-accra"
    html = await scrape_with_playwright(meqasa_url, 'div[data-testid="listing-card"]')
    if not html:
        html = scrape_with_requests(meqasa_url)
    listings.extend(parse_meqasa_listings(html))

    # Tonaton (try Playwright first, then requests)
    tonaton_url = "https://tonaton.com/property"
    html = await scrape_with_playwright(tonaton_url, 'div[class*="card"]')
    if not html:
        html = scrape_with_requests(tonaton_url)
    listings.extend(parse_tonaton_listings(html))

    print(f"✅ Scraped {len(listings)} listings")
    return listings

if __name__ == "__main__":
    asyncio.run(scrape_all())