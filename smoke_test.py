import asyncio
from scrapers.meqasa_scraper import main as run_meqasa
from scrapers.tonaton_scraper import main as run_tonaton
from scrapers.jiji_scraper import main as run_jiji

async def test_all():
    print("🚀 Starting Smoke Test for all scrapers (1 page each)...")
    
    print("\n--- Testing Meqasa ---")
    try:
        await run_meqasa(max_pages=1)
    except Exception as e:
        print(f"❌ Meqasa Test Failed: {e}")

    print("\n--- Testing Tonaton ---")
    try:
        await run_tonaton(max_pages=1)
    except Exception as e:
        print(f"❌ Tonaton Test Failed: {e}")

    print("\n--- Testing Jiji ---")
    try:
        # Note: Jiji uses scroll_count instead of max_pages
        await run_jiji(scroll_count=2) 
    except Exception as e:
        print(f"❌ Jiji Test Failed: {e}")

    print("\n✅ Smoke test cycle complete. Check your GCS bucket for new files.")

if __name__ == "__main__":
    asyncio.run(test_all())
