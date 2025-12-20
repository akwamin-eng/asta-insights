import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_gpc_pages(max_pages=3):
    """
    Scrapes Ghana Property Centre with Pagination and improved Title extraction.
    """
    all_results = []
    
    async with async_playwright() as p:
        # headless=False to visually monitor progress
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await stealth_async(page)

        base_url = "https://ghanapropertycentre.com/for-sale"
        print(f"🚀 [GPC] Starting crawl at: {base_url}")
        
        await page.goto(base_url, timeout=60000, wait_until="domcontentloaded")

        current_page = 1
        while current_page <= max_pages:
            print(f"--- Processing Page {current_page} ---")
            
            # 1. Wait for content to settle
            try:
                await page.wait_for_selector("text=Results", timeout=15000)
            except:
                print("⚠️ Page took too long to render.")

            # 2. Scroll to load lazy images/items
            for _ in range(3):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(0.5)

            # 3. Find Cards via Anchor
            anchors = await page.locator("a:has-text('More details')").all()
            print(f"   Found {len(anchors)} listings on this page.")

            page_data = []
            for i, anchor in enumerate(anchors):
                try:
                    # Get the card container (3 levels up from the button)
                    card = anchor.locator("xpath=../../..")
                    
                    # --- IMPROVED EXTRACTION ---
                    # 1. Title: Look for Header tags (h2, h3, h4) inside the card
                    # This fixes the "Unknown" issue
                    title = "Unknown"
                    header_el = card.locator("h2, h3, h4, .property-title").first
                    if await header_el.count() > 0:
                        title = await header_el.inner_text()
                    
                    # 2. Price: Look for price class or text
                    price = "0"
                    price_el = card.locator(".price, span[itemprop='price']").first
                    if await price_el.count() > 0:
                        price = await price_el.inner_text()
                    else:
                        # Fallback: scan text for currency
                        text = await card.inner_text()
                        for line in text.split('\n'):
                            if "GH₵" in line or "$" in line:
                                price = line
                                break
                    
                    # 3. Location
                    location = "Unknown"
                    loc_el = card.locator("address, .location").first
                    if await loc_el.count() > 0:
                        location = await loc_el.inner_text()

                    # Clean data
                    if title != "Unknown":
                        page_data.append({
                            "title": title.strip(),
                            "price": price.strip(),
                            "location": location.strip(),
                            "page": current_page
                        })

                except Exception as e:
                    continue
            
            all_results.extend(page_data)
            print(f"   ✅ Extracted {len(page_data)} items from page {current_page}.")

            # 4. PAGINATION LOGIC
            # Look for "Next" button or ">>"
            # Common selectors: 'ul.pagination li.next a', or text='Next'
            if current_page < max_pages:
                try:
                    next_btn = page.locator("ul.pagination li a[rel='next'], a:has-text('Next'), a:has-text('›')").last
                    
                    if await next_btn.is_visible():
                        print("   🖱️ Clicking Next Page...")
                        await next_btn.click()
                        current_page += 1
                        # Wait for the page number to update or url to change
                        await asyncio.sleep(3) 
                    else:
                        print("   🛑 No 'Next' button found. Stopping.")
                        break
                except Exception as e:
                    print(f"   🛑 Pagination error: {e}")
                    break
            else:
                break

        print(f"\n🎉 Total Extracted: {len(all_results)} items.")
        
        # Display sample
        if all_results:
            print(f"   Sample: {all_results[0]['title']} - {all_results[0]['price']}")

        await browser.close()
        return all_results

if __name__ == "__main__":
    asyncio.run(scrape_gpc_pages(max_pages=2))
