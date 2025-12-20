import asyncio
import json
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

START_PAGE = 1
END_PAGE = 332  # Set to 332 for full dump, or 5 for a quick test
OUTPUT_FILE = "gpc_master_dump_2025_v2.jsonl"

async def extract_card_details(card, page_num):
    try:
        text_content = await card.inner_text()
        full_text = text_content.replace("\n", " ")
        
        # --- THE FIX: ROBUST URL EXTRACTION ---
        url = ""
        
        # Method A: Get href from the "More details" button (Most reliable)
        more_btn = card.locator("a:has-text('More details')").first
        if await more_btn.count() > 0:
            url = await more_btn.get_attribute("href")
        
        # Method B: Get href from the Title
        if not url:
            header = card.locator("h2 a, h3 a, h4 a, .property-title a").first
            if await header.count() > 0:
                url = await header.get_attribute("href")

        # Normalize (Handle relative paths)
        if url and not url.startswith("http"):
            url = f"https://ghanapropertycentre.com{url}"
            
        # skip if still empty
        if not url:
            return None

        # --- EXTRACT OTHER DETAILS ---
        title_el = card.locator("h2, h3, h4").first
        title = await title_el.inner_text() if await title_el.count() > 0 else "Unknown Title"
        
        price_match = re.search(r'((?:GH₵|\$)\s?[\d,]+(?:\.\d{2})?)', full_text)
        price = price_match.group(1) if price_match else "Contact for Price"
        
        beds = re.search(r'(\d+)\s?(?:Bedrooms|Beds)', full_text, re.IGNORECASE)
        baths = re.search(r'(\d+)\s?(?:Bathrooms|Baths)', full_text, re.IGNORECASE)

        return {
            "url": url,
            "title": title.strip(),
            "price": price.strip(),
            "location": "Accra", # Simplified for robustness
            "bedrooms": beds.group(1) if beds else None,
            "bathrooms": baths.group(1) if baths else None,
            "page": page_num,
            "scraped_at": datetime.now().isoformat(),
            "raw_text_snippet": full_text[:200]
        }
    except Exception:
        return None

async def run_master_dump():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await stealth_async(page)

        print(f"🚀 STARTING DUMP to: {OUTPUT_FILE}")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for page_num in range(START_PAGE, END_PAGE + 1):
                print(f"--- Processing Page {page_num} ---")
                try:
                    await page.goto(f"https://ghanapropertycentre.com/for-sale?page={page_num}", timeout=60000)
                    
                    # Wait for data
                    try:
                        await page.wait_for_selector("a:has-text('More details')", timeout=15000)
                    except:
                        print("   ⚠️ Timeout (Page load issue)")
                        continue

                    # Find all cards
                    anchors = await page.locator("a:has-text('More details')").all()
                    
                    count = 0
                    for anchor in anchors:
                        card = anchor.locator("xpath=../../..")
                        data = await extract_card_details(card, page_num)
                        if data:
                            f.write(json.dumps(data) + "\n")
                            count += 1
                    
                    print(f"   ✅ Saved {count} items.")
                    await asyncio.sleep(1) # Polite delay
                except Exception as e:
                    print(f"   �� Error on page {page_num}: {e}")

        await browser.close()
        print("\n🎉 Dump Complete.")

if __name__ == "__main__":
    asyncio.run(run_master_dump())
