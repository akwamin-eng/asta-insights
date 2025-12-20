import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_gpc(search_type: str = "for-sale", headless: bool = True):
    """
    Robust scraper for Ghana Property Centre.
    Args:
        search_type: 'for-sale' or 'for-rent'
        headless: Set to False to visually debug the browser actions.
    """
    extracted_data = []
    
    async with async_playwright() as p:
        # Launch browser with slightly slower type delay to mimic humans
        browser = await p.chromium.launch(headless=headless, slow_mo=50)
        
        # specific context to bypass basic bot detection
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="en-GB",
            timezone_id="Africa/Accra"
        )
        
        page = await context.new_page()
        
        # Apply stealth to mask automation signals
        await stealth_async(page)

        # Construct URL
        base_url = "https://www.ghanapropertycentre.com"
        target_url = f"{base_url}/{search_type}"
        print(f"🚀 [GPC] Navigating to: {target_url}")

        try:
            # 1. Navigation with robust timeout
            # We use 'domcontentloaded' because GPC images can take forever to load
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            # 2. Smart Wait: Wait specifically for the property list container
            # Fallback selectors included for 2025 layout changes
            print("⏳ [GPC] Waiting for listings to hydrate...")
            try:
                await page.wait_for_selector(
                    "div.property-list-item, div.content-box, div.property-listing", 
                    timeout=20000
                )
            except Exception:
                print("⚠️ [GPC] Timeout waiting for selectors. Taking debug screenshot...")
                await page.screenshot(path="debug_gpc_timeout.png")
                return []

            # 3. Handle Cookie Consent if present (common blocker)
            try:
                cookie_btn = page.locator("button.accept-cookies, #cookie-consent-accept")
                if await cookie_btn.is_visible():
                    await cookie_btn.click()
                    await asyncio.sleep(1)
            except:
                pass

            # 4. Extract Listings
            # We target the specific listing cards
            listings = await page.locator("div.property-list-item, div.property-listing").all()
            print(f"🔎 [GPC] Found {len(listings)} potential property nodes.")

            if len(listings) == 0:
                # Immediate visual feedback if we failed to parse
                await page.screenshot(path="debug_gpc_zero_items.png")
                print("❌ [GPC] Zero items found. Saved screenshot to 'debug_gpc_zero_items.png'")
                return []

            for i, listing in enumerate(listings[:20]): # Limit to 20 for safety
                try:
                    # Robust Selectors with Fallbacks
                    
                    # Title
                    title_el = listing.locator("h4.content-title, div.property-title, h3 a").first
                    title = await title_el.inner_text() if await title_el.count() > 0 else "Unknown Title"
                    
                    # Link
                    link_el = listing.locator("a[itemprop='url'], .content-title a").first
                    link = await link_el.get_attribute("href") if await link_el.count() > 0 else ""
                    full_link = f"{base_url}{link}" if link and not link.startswith("http") else link

                    # Price
                    price_el = listing.locator(".price, span[itemprop='price']").first
                    price = await price_el.inner_text() if await price_el.count() > 0 else "0"

                    # Location
                    loc_el = listing.locator("address, .location, .property-location").first
                    location = await loc_el.inner_text() if await loc_el.count() > 0 else "Unknown Location"

                    # Data Cleaning
                    if title != "Unknown Title":
                        extracted_data.append({
                            "source": "GhanaPropertyCentre",
                            "title": title.strip(),
                            "price_raw": price.strip().replace("\n", ""),
                            "location": location.strip(),
                            "url": full_link,
                            "scraped_at": datetime.now().isoformat()
                        })

                except Exception as e:
                    print(f"⚠️ [GPC] Skipped item {i} due to error: {e}")
                    continue

        except Exception as e:
            print(f"🔥 [GPC] Critical Error: {e}")
            await page.screenshot(path="debug_gpc_critical_error.png")
        
        finally:
            await context.close()
            await browser.close()
            
    return extracted_data
