# scrape_ghana_listings.py (Updated skeleton for Playwright)
import asyncio
from playwright.async_api import async_playwright
import requests # Keep for potential non-Cloudflare sites or metadata fetching later
from bs4 import BeautifulSoup # Keep for parsing HTML once obtained via Playwright
import time
import re

async def scrape_with_playwright_improved(url, content_loaded_selector, max_retries=2):
    """
    Scrape using Playwright, waiting for content to load after potential Cloudflare challenge.
    Includes basic retry logic.
    """
    for attempt in range(max_retries + 1):
        try:
            print(f"  🌐 Attempt {attempt+1}/{max_retries+1} for {url} with Playwright...")
            async with async_playwright() as p:
                # Launch browser with a more realistic context
                browser = await p.chromium.launch(
                    headless=True, # Set to False if you need to visually debug the challenge
                    # Add arguments if stealth is needed later
                    # args=['--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(
                    # Use a common user agent
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                print(f"    Navigating to {url}...")
                await page.goto(url, timeout=30000) # Increased timeout

                print(f"    Waiting for content selector '{content_loaded_selector}' (attempt {attempt+1})...")
                # Wait for an element that indicates the *listings* have loaded
                # This is the critical part - you need the *right* selector from inspecting the site.
                # Example for Meqasa: Could be a div containing the search results grid.
                # Example for Tonaton: Could be a div containing the item list.
                await page.wait_for_selector(content_loaded_selector, timeout=30000)

                print("    ✅ Content seems to have loaded. Attempting to get HTML...")
                content = await page.content()
                print(f"    📥 Playwright successfully fetched {len(content)} characters after potential challenge/resolution.")
                await browser.close()
                return content

        except Exception as e:
            print(f"    ⚠️ Playwright attempt {attempt+1} failed for {url}: {e}")
            if attempt < max_retries:
                print(f"      Sleeping before retry...")
                await asyncio.sleep(5) # Brief delay before retry
            else:
                print(f"    ❌ Playwright failed for {url} after {max_retries+1} attempts.")
                try:
                    await browser.close() # Ensure browser closes on failure
                except:
                    pass # Ignore error if browser wasn't created yet
                return None
    return None # Should not reach here if loop is correct

# --- Parsing Functions (Need Update Based on Live HTML Structure) ---
# Example placeholder - you need to inspect the actual HTML to write these correctly.
def parse_meqasa_listings(html):
    """Parse Meqasa listings from HTML obtained via Playwright."""
    if not html:
        print("   📝 parse_meqasa_listings: No HTML provided.")
        return []
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    # --- CORRECTED: Use the actual container selector for individual listings ---
    # The outer <div> tag with class 'mqs-prop-image-wrapper' seems to be the individual listing container.
    listing_containers = soup.select('div.mqs-prop-image-wrapper')
    print(f"   🔍 Meqasa: Found {len(listing_containers)} potential listing containers.")
    for container in listing_containers:
        try:
            # --- CORRECTED: Use the actual selectors for price, title, link ---
            # Title/Link is inside h2 > a
            title_link_elem = container.select_one('h2 a')
            title = title_link_elem.get_text(strip=True) if title_link_elem else "No Title"
            relative_link = title_link_elem.get('href') if title_link_elem else None
            link = 'https://meqasa.com' + relative_link if relative_link else None

            # Price is trickier. It's inside p.h3, but not in a dedicated span.
            # Find the 'Price' span, then get the next sibling text node.
            price_label_elem = container.select_one('p.h3 span:-soup-contains("Price")')
            price_text = "N/A"
            if price_label_elem:
                # The price text is directly after the 'Price' span within the <p.h3>
                price_paragraph = price_label_elem.parent # This is the <p class="h3">
                # Iterate through the direct children/text nodes of the paragraph
                for content in price_paragraph.contents:
                    if content == price_label_elem:
                        # This is the 'Price' label itself, get the next node
                        continue
                    elif isinstance(content, str) and content.strip():
                         # This is a text node, likely the price
                         price_text = content.strip()
                         break

            # Clean price: remove currency, commas, etc., keep only numbers and decimal point.
            price_cleaned = re.sub(r'[^\d.]', '', price_text) # e.g., "GH₵195,000 / month" -> "195000"
            price = float(price_cleaned) if price_cleaned else None # Convert to float

            # Optional: Extract bedrooms from title using regex if needed
            bedrooms_match = re.search(r'(\d+)\s*bedroom', title, re.IGNORECASE)
            bedrooms = int(bedrooms_match.group(1)) if bedrooms_match else None

            # Optional: Extract location from title using regex if needed (less reliable)
            # Or if there's a separate location element, use that selector.
            # location_match = re.search(r'in\s+(.+)$', title, re.IGNORECASE)
            # location = location_match.group(1).strip() if location_match else "N/A"

            listings.append({
                "source": "meqasa",
                "title": title,
                "price": price,
                "bedrooms": bedrooms, # Add bedrooms if extracted
                "url": link # Add the link to the specific listing
                # "location": location # Add if extracted
            })
        except Exception as e:
            print(f"     ⚠️ Error parsing a Meqasa listing: {e}")
            import traceback # Optional: print full traceback for debugging
            traceback.print_exc()
            continue
    print(f"   ✅ Meqasa: Parsed {len(listings)} listings")
    return listings

def parse_tonaton_listings(html):
    """Parse Tonaton listings from HTML obtained via Playwright."""
    if not html:
        print("   📝 parse_tonaton_listings: No HTML provided.")
        return []
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    # --- CORRECTED: Use the actual container selector for individual listings ---
    # The outer <a> tag is the individual listing container.
    listing_containers = soup.select('a.product__item') # Use the <a> tag with the specific class
    print(f"   🔍 Tonaton: Found {len(listing_containers)} potential listing containers.")
    for container in listing_containers:
        try:
            # --- CORRECTED: Use the actual selectors for price, title, location ---
            # Price is inside span.product__title
            price_elem = container.select_one('span.product__title')
            price_text = price_elem.get_text(strip=True) if price_elem else "N/A"
            # Clean price: remove currency, commas, etc., keep only numbers and decimal point.
            price_cleaned = re.sub(r'[^\d.]', '', price_text) # e.g., "GH₵ 350,000" -> "350000"
            price = float(price_cleaned) if price_cleaned else None # Convert to float

            # Description/Title is inside p.product__description
            title_elem = container.select_one('p.product__description')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"

            # Location is inside p.product__location
            location_elem = container.select_one('p.product__location')
            location = location_elem.get_text(strip=True) if location_elem else "No Location"

            # Link is the href of the main container <a> tag (relative path)
            link = container.get('href')
            if link:
                link = 'https://tonaton.com' + link # Prepend base URL if relative

            # Optional: Extract size from tags
            size_elem = container.select_one('div.product__tags span:nth-child(2)') # e.g., 2nd span contains size
            size_text = size_elem.get_text(strip=True) if size_elem else "N/A"
            # Extract numeric part if it's like "230 sqm"
            size_match = re.search(r'(\d+)', size_text)
            size_sqm = int(size_match.group(1)) if size_match else None

            listings.append({
                "source": "tonaton",
                "title": title,
                "price": price,
                "location": location,
                "size_sqm": size_sqm, # Add size if extracted
                "url": link # Add the link to the specific listing
            })
        except Exception as e:
            print(f"     ⚠️ Error parsing a Tonaton listing: {e}")
            import traceback # Optional: print full traceback for debugging
            traceback.print_exc()
            continue
    print(f"   ✅ Tonaton: Parsed {len(listings)} listings")
    return listings

def parse_jiji_listings(html):
    """Parse Jiji listings from HTML obtained via Playwright."""
    if not html:
        print("   📝 parse_jiji_listings: No HTML provided.")
        return []
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    # --- CORRECTED: Use the actual container selector for individual listings ---
    # The outer <a> tag is the individual listing container.
    listing_containers = soup.select('a.qa-advert-list-item') # Use the <a> tag with the specific class
    print(f"   🔍 Jiji: Found {len(listing_containers)} potential listing containers.")
    for container in listing_containers:
        try:
            # --- CORRECTED: Use the actual selectors for price, title, location ---
            # Price is inside div.qa-advert-price
            price_elem = container.select_one('div.qa-advert-price')
            price_text = price_elem.get_text(strip=True) if price_elem else "N/A"
            # Clean price: remove currency, commas, etc., keep only numbers and decimal point.
            # This regex keeps digits, periods, and commas (for further cleaning if needed)
            price_cleaned = re.sub(r'[^\d.]', '', price_text) # e.g., "GH₵ 2,700" -> "2700"
            price = float(price_cleaned) if price_cleaned else None # Convert to float

            # Title is inside div.qa-advert-title (specifically b-advert-title-inner)
            title_elem = container.select_one('div.qa-advert-title div.b-advert-title-inner')
            title = title_elem.get_text(strip=True) if title_elem else "No Title"

            # Location is inside div.b-list-advert__region__text
            location_elem = container.select_one('div.b-list-advert__region__text')
            location = location_elem.get_text(strip=True) if location_elem else "No Location"

            # Link is the href of the main container <a> tag
            link = container.get('href')
            if link:
                link = 'https://jiji.com.gh' + link # Prepend base URL if relative

            # Optional: Extract other details like bedrooms from title using regex if needed
            bedrooms_match = re.search(r'(\d+)bdrm', title, re.IGNORECASE)
            bedrooms = int(bedrooms_match.group(1)) if bedrooms_match else None

            listings.append({
                "source": "jiji",
                "title": title,
                "price": price,
                "location": location,
                "bedrooms": bedrooms, # Add bedrooms if extracted
                "url": link # Add the link to the specific listing
            })
        except Exception as e:
            print(f"     ⚠️ Error parsing a Jiji listing: {e}")
            import traceback # Optional: print full traceback for debugging
            traceback.print_exc()
            continue
    print(f"   ✅ Jiji: Parsed {len(listings)} listings")
    return listings

async def scrape_all():
    listings = []

    # --- Tonaton ---
    tonaton_url = "https://tonaton.com/c_real-estate" # Use the corrected URL
    # Find an element that appears after any potential challenge and listings load on Tonaton.
    # Based on common layout structures, a main content area often holds the list.
    # Inspecting the actual page structure is ideal, but `div.l-main` or similar is often used.
    # The individual items are <a class='product__item'>.
    tonaton_content_loaded_selector = "div.l-main" # Initial guess for main content area - REPLACE with actual selector found via inspection!
    print(f"🔍 Starting Tonaton scrape...")
    html = await scrape_with_playwright_improved(tonaton_url, tonaton_content_loaded_selector)
    if html:
        listings.extend(parse_tonaton_listings(html))
    else:
        print("  ❌ Playwright failed for Tonaton.")

    # --- Meqasa (Sale) ---
    meqasa_sale_url = "https://meqasa.com/properties-for-sale-in-ghana" # Use the corrected URL
    # Find an element that appears after Cloudflare and listings load on Meqasa (Sale).
    # Inspect the HTML after the challenge passes and listings appear.
    # Common names might be 'div.search-results', 'div.mqs-search-results', 'main', etc.
    meqasa_sale_content_loaded_selector = "div.mqs-search-results" # Initial guess - REPLACE with actual selector found via inspection!
    print(f"🔍 Starting Meqasa (Sale) scrape...")
    html = await scrape_with_playwright_improved(meqasa_sale_url, meqasa_sale_content_loaded_selector)
    if html:
        listings.extend(parse_meqasa_listings(html)) # Assumes parsing logic handles 'sale' correctly or is generic
    else:
        print("  ❌ Playwright failed for Meqasa (Sale).")

    # --- Meqasa (Rent) ---
    meqasa_rent_url = "https://meqasa.com/properties-for-rent-in-ghana" # Use the corrected URL
    # Find an element that appears after Cloudflare and listings load on Meqasa (Rent).
    # Inspect the HTML after the challenge passes and listings appear.
    # Often the same container selector works for both rent/sale if they use the same template.
    meqasa_rent_content_loaded_selector = "div.mqs-search-results" # Initial guess - REPLACE with actual selector found via inspection!
    print(f"🔍 Starting Meqasa (Rent) scrape...")
    html = await scrape_with_playwright_improved(meqasa_rent_url, meqasa_rent_content_loaded_selector)
    if html:
        listings.extend(parse_meqasa_listings(html)) # Assumes parsing logic handles 'rent' correctly or is generic
    else:
        print("  ❌ Playwright failed for Meqasa (Rent).")

    # --- Jiji ---
    jiji_url = "https://jiji.com.gh/houses-apartments-for-rent" # Use the corrected URL
    # Find an element that appears after any potential challenge and listings load on Jiji.
    # Based on common structure, the list container often has a class like 'b-list-advert' or similar.
    # The individual items are <a class='qa-advert-list-item'>.
    jiji_content_loaded_selector = "div.b-list-advert" # Selector for the container holding the list of items
    print(f"🔍 Starting Jiji scrape...")
    html = await scrape_with_playwright_improved(jiji_url, jiji_content_loaded_selector)
    if html:
        listings.extend(parse_jiji_listings(html))
    else:
        print("  ❌ Playwright failed for Jiji.")

    print(f"✅ Scraped {len(listings)} listings from sources that bypassed protection (likely Playwright).")
    return listings

if __name__ == "__main__":
    # Run the scrape
    scraped_data = asyncio.run(scrape_all())
    # Optional: Print a sample or save to file for testing
    if scraped_data:
        print("\n--- Sample of Scraped Data ---")
        for i, listing in enumerate(scraped_data[:3]): # Print first 3 listings
            print(f"Listing {i+1}: {listing}")
        print(f"\n... and {max(0, len(scraped_data) - 3)} more.")
    else:
        print("\n--- No Data Scraped ---")