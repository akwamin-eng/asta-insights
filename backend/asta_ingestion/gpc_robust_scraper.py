import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_gpc_anchored(headless=False):
    """
    Scrapes Ghana Property Centre using text anchors ("More details", "GH₵")
    instead of brittle CSS class names.
    """
    results = []
    
    async with async_playwright() as p:
        # headless=False allows you to see if a CAPTCHA appears
        browser = await p.chromium.launch(headless=headless, slow_mo=50)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await stealth_async(page)

        target_url = "https://ghanapropertycentre.com/for-sale?page=3"
        print(f"🚀 [GPC] Navigating to: {target_url}")
        
        try:
            await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")

            # 1. Wait for visual confirmation of content
            print("⏳ [GPC] Waiting for 'Results' text...")
            try:
                await page.wait_for_selector("text=Results", timeout=15000)
            except:
                print("⚠️ 'Results' text not found. Checking for captcha...")
            
            # 2. Scroll to trigger lazy loading
            print("⬇️ [GPC] Scrolling to load listings...")
            for _ in range(4):
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(1)

            # 3. TEXT ANCHOR STRATEGY
            # Find all elements containing "More details" and "GH₵"
            # This bypasses obfuscated class names like .x-123-y
            print("🔎 [GPC] Locating cards via text anchors...")
            
            # We look for the "More details" button which is consistent
            anchors = await page.locator("a:has-text('More details')").all()
            print(f"   Found {len(anchors)} anchor points.")

            for i, anchor in enumerate(anchors):
                try:
                    # The card is usually a parent of the "More details" button
                    # We traverse up 3 levels to get the full card container
                    card = anchor.locator("xpath=../../..") 
                    
                    text_content = await card.inner_text()
                    lines = [l.strip() for l in text_content.split('\n') if l.strip()]

                    # Heuristic parsing (Scan lines for keywords)
                    title = "Unknown"
                    price = "0"
                    location = "Unknown"

                    for line in lines:
                        if "GH₵" in line or "$" in line:
                            price = line
                        elif "Bedroom" in line or "Land" in line or "House" in line:
                            # Usually the longest line with these words is the title
                            if len(line) > len(title):
                                title = line
                        elif "Accra" in line or "Region" in line:
                            location = line

                    if price != "0":
                        results.append({
                            "id": i,
                            "title": title,
                            "price": price,
                            "location": location,
                            "source": "GPC"
                        })
                except Exception as e:
                    continue

        except Exception as e:
            print(f"🔥 [GPC] Error: {e}")
            await page.screenshot(path="debug_gpc_crash.png")

        finally:
            await browser.close()
            
    return results

if __name__ == "__main__":
    data = asyncio.run(scrape_gpc_anchored(headless=False))
    print(f"\n✅ Extracted {len(data)} items:")
    for item in data[:5]:
        print(f"   - {item['title']} ({item['price']})")
