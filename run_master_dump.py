import asyncio
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).parent))

from scrapers.jiji_retest import main as run_jiji
from scrapers.tonaton_stealth import main as run_tonaton
from scrapers.meqasa_stealth import main as run_meqasa
from scrapers.ghanapropertycentre_stealth import main as run_gpc

async def run_all():
    print("🚀 STARTING MASTER DATA DUMP (2025 Market Trends Edition) 🚀")
    
    tasks = [
        ("Jiji", run_jiji()),
        ("Tonaton", run_tonaton()),
        ("Meqasa", run_meqasa()),
        ("GPC", run_gpc(max_pages=50))  # GPC is high quality, get more pages
    ]
    
    for name, task in tasks:
        print(f"\n--- Processing {name} ---")
        try:
            await task
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            
    print("\n✅ MASTER DUMP COMPLETE. Check GCS for all site JSONs.")

if __name__ == "__main__":
    asyncio.run(run_all())
