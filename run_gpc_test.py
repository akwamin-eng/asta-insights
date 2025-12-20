import asyncio
import json
from backend.asta_ingestion.gpc_scraper import scrape_gpc

async def main():
    print("--- STARTING GPC ISOLATED TEST ---")
    
    # Test 1: For Sale
    print("\n1. Testing 'For Sale'...")
    sale_data = await scrape_gpc(search_type="for-sale", headless=True)
    
    if sale_data:
        print(f"✅ Success! Extracted {len(sale_data)} items.")
        print(f"   Sample: {sale_data[0]['title']} - {sale_data[0]['price_raw']}")
        
        # Save to JSON for inspection
        with open("gpc_test_data.json", "w") as f:
            json.dump(sale_data, f, indent=2)
        print("   Saved data to gpc_test_data.json")
    else:
        print("❌ Failed to extract 'For Sale' data. Check debug screenshots.")

    # Optional: Test Rent
    # print("\n2. Testing 'For Rent'...")
    # rent_data = await scrape_gpc(search_type="for-rent")
    # print(f"   Extracted {len(rent_data)} items.")

if __name__ == "__main__":
    asyncio.run(main())
