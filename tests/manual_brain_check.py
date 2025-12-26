import asyncio
import os
import sys

# Ensure we can import services.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import process_text_to_property

async def run_test():
    # 1. Simulate a messy WhatsApp message
    fake_message = "Hi putting up my place for rent. It is a 2 bedroom in East Legon Hills near the school. Price is 4500 ghana cedis. Has a generator and water tank."
    
    print(f"🧪 TESTING INPUT: {fake_message}\n")
    print("... Calling Asta Engine ...\n")

    # 2. Run the new logic
    result = await process_text_to_property(fake_message)

    # 3. Validation
    if result:
        print("\n✅ SUCCESS! Engine returned:")
        print(f"   🏠 Title: {result.get('title')}")
        print(f"   📍 Clean Location: {result.get('location_name')}")
        print(f"   🌍 Coordinates: {result.get('lat')}, {result.get('long')}")
        print(f"   🏷️  Features: {result.get('vibe_features')}")
        
        if result.get('lat') != 0:
            print("   🎉 GEOCODING WORKED (Not in the ocean!)")
        else:
            print("   ⚠️ GEOCODING FAILED (Returned 0,0)")
    else:
        print("\n❌ FAILED: Engine returned None.")

if __name__ == "__main__":
    asyncio.run(run_test())
