# scrape_rent_only.py
"""
Standalone script to scrape ONLY GhanaPropertyCentre.com 'for-rent' listings.
Useful for testing or running rent scraping independently.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import the scraping function
from scrapers.ghanapropertycentre_scraper import scrape_listings, BASE_URL_RENT, save_raw_data_to_gcs

async def main():
    """Main function to scrape only for-rent listings."""
    print("--- Starting GhanaPropertyCentre Rent-Only Scraper ---")
    
    # --- Scrape ONLY For Rent Listings ---
    print(f"  🕷️  Target URL: {BASE_URL_RENT}")
    rent_properties = await scrape_listings(BASE_URL_RENT, "for_rent", max_pages=300) # Scrape up to 300 pages for rent
    save_raw_data_to_gcs(rent_properties, "for_rent")
    
    print(f"\n✅ Rent-only scraping completed. Total properties scraped: {len(rent_properties)}")

if __name__ == "__main__":
    asyncio.run(main())
