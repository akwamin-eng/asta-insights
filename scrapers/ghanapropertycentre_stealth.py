import asyncio
import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.cloud import storage
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode

sys.path.append(str(Path(__file__).parent.parent))
from scrapers.stealth_config import get_stealth_browser_config, get_human_run_config, retry_with_backoff

load_dotenv()
bucket = storage.Client().bucket(os.getenv("GCS_BUCKET_NAME"))

SITE_NAME = "ghanapropertycentre.com"
SCHEMA = {
    "name": "GPC Data Dump",
    "baseSelector": "div.wp-block.property",
    "fields": [
        {"name": "title", "selector": "h4[itemprop='name'] a", "type": "text"},
        {"name": "link", "selector": "a[itemprop='url']", "type": "attribute", "attribute": "href"},
        {"name": "price_raw", "selector": ".price", "type": "text"},
        {"name": "location", "selector": "address", "type": "text"},
        {"name": "features", "selector": "ul.aux-info", "type": "text"}
    ]
}

def parse_stats(item):
    # Regex to extract numeric beds/baths/toilets from the features string
    f_str = str(item.get('features', '')).lower()
    item['beds'] = int(m.group(1)) if (m := re.search(r'(\d+)\s*bed', f_str)) else None
    item['baths'] = int(m.group(1)) if (m := re.search(r'(\d+)\s*bath', f_str)) else None
    
    price_str = item.get('price_raw', '')
    item['currency'] = 'USD' if '$' in price_str else 'GHS'
    num_price = re.sub(r'[^\d]', '', price_str)
    item['price_numeric'] = int(num_price) if num_price else None
    return item

@retry_with_backoff(retries=5)
async def scrape_page(crawler, url, run_cfg):
    result = await crawler.arun(url=url, config=run_cfg)
    if not result.success: raise Exception(f"Crawl Error: {result.error_message}")
    return result

async def main(max_pages=20):
    targets = {"for_sale": "https://www.ghanapropertycentre.com/for-sale", "for_rent": "https://www.ghanapropertycentre.com/for-rent"}
    browser_cfg = get_stealth_browser_config()

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for l_type, base_url in targets.items():
            all_data = []
            current_url = base_url
            for p in range(1, max_pages + 1):
                res = await scrape_page(crawler, current_url, get_human_run_config(JsonCssExtractionStrategy(SCHEMA)))
                if not res.extracted_content: break
                
                items = [parse_stats(i) for i in json.loads(res.extracted_content) if i.get('title')]
                for i in items: i.update({"type": l_type, "scraped_at": datetime.now(timezone.utc).isoformat()})
                all_data.extend(items)
                print(f"✅ GPC {l_type} | Page {p}: Found {len(items)} items")

                # Robust Next Page Finder
                soup = BeautifulSoup(res.html, 'html.parser')
                next_tag = soup.find('a', {'title': re.compile('Next', re.I)}) or soup.select_one('li.next a')
                if next_tag and next_tag.get('href'):
                    current_url = urljoin(base_url, next_tag['href'])
                else: break
            
            if all_data:
                blob_path = f"raw/property_listings/{SITE_NAME}/{l_type}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                bucket.blob(blob_path).upload_from_string(json.dumps(all_data, indent=2))
