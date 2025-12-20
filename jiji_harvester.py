import asyncio
import json
import re
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
BASE_URL = "https://jiji.com.gh/houses-apartments-for-rent"
MAX_PAGES = 5  
OUTPUT_FILE = "jiji_dump_raw.json"

def clean_price(price_str):
    if not price_str: return 0
    clean = re.sub(r'[^\d]', '', price_str)
    return int(clean) if clean else 0

async def scrape_jiji():
    data_dump = []
    
    async with async_playwright() as p:
        # Launch NON-HEADLESS so you can interact with the browser
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"🕵️  Navigating to {BASE_URL}...")
        await page.goto(BASE_URL, timeout=60000)

        # --- THE FIX: HUMAN INTERVENTION BLOCK ---
        print("\n" + "="*60)
        print("🛑  CLOUDFLARE CHECKPOINT")
        print("1. Look at the browser window.")
        print("2. If you see 'Verify you are human', click the box.")
        print("3. Wait until you actually see the HOUSE LISTINGS.")
        print("="*60)
        input("🟢  Press ENTER here in the terminal once you see the listings... ")
        # -----------------------------------------

        for i in range(MAX_PAGES):
            print(f"📄 Scraping Page {i+1}...")
            
            # Wait for items to ensure page is loaded
            try:
                await page.wait_for_selector('div.b-list-advert__gallery__item', timeout=10000)
            except:
                print("   ⚠️ Timed out waiting for items.")
            
            listings = await page.evaluate("""() => {
                const items = Array.from(document.querySelectorAll('div.b-list-advert__gallery__item'));
                return items.map(item => {
                    const titleEl = item.querySelector('.qa-advert-title');
                    const priceEl = item.querySelector('.qa-advert-price');
                    const locEl = item.querySelector('.b-list-advert__item-region');
                    const linkEl = item.querySelector('a.b-list-advert__item-title');
                    const imgEl = item.querySelector('img');

                    return {
                        title: titleEl ? titleEl.innerText.trim() : "Unknown",
                        price_raw: priceEl ? priceEl.innerText.trim() : "0",
                        location: locEl ? locEl.innerText.trim() : "Unknown",
                        url: linkEl ? linkEl.href : "",
                        image_url: imgEl ? imgEl.src : ""
                    };
                });
            }""")
            
            page_count = 0
            for item in listings:
                if item['title'] == "Unknown": continue
                normalized_item = {
                    "source": "Jiji Ghana",
                    "title": item['title'],
                    "price": clean_price(item['price_raw']),
                    "location": item['location'],
                    "url": item['url'],
                    "image": item['image_url'],
                    "external_id": item['url'].split("/")[-1].replace(".html", "") if item['url'] else "unknown"
                }
                data_dump.append(normalized_item)
                page_count += 1
                
            print(f"   ✅ Collected {page_count} listings.")

            # Pagination
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                next_button = page.locator('.b-pagination__item-next, a:has-text("Next")').first
                if await next_button.is_visible():
                    await next_button.click()
                    await asyncio.sleep(3)
                else:
                    print("   🛑 No 'Next' button found. Stopping.")
                    break
            except Exception as e:
                print(f"   ⚠️ Pagination error: {e}")
                break

        await browser.close()
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data_dump, f, indent=2)
    
    print(f"\n🎉 DONE! Scraped {len(data_dump)} properties.")
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scrape_jiji())
