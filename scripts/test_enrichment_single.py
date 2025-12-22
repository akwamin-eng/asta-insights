import os
import json
from dotenv import load_dotenv
from scripts.enricher import get_asta_insights
from processing.location_intelligence import LocationIntelligence

load_dotenv()

def main():
    print("🔬 DIAGNOSTIC: Testing AI Modules on Single Item...\n")
    
    # Dummy Listing
    test_title = "Executive 4 Bedroom House with Pool"
    test_location = "East Legon, Accra"
    test_price = "450000"

    # 1. Test Location Intelligence (Local/Database)
    print("--- TESTING LOCATION INTELLIGENCE ---")
    try:
        loc_intel = LocationIntelligence()
        context = loc_intel.get_location_context(test_location)
        print("✅ Location Result:", json.dumps(context, indent=2))
    except Exception as e:
        print(f"❌ Location Module Failed: {e}")

    print("\n" + "="*30 + "\n")

    # 2. Test Gemini (API Call)
    print("--- TESTING GEMINI API ---")
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ CRITICAL: GOOGLE_API_KEY is missing from .env!")
        return

    try:
        print(f"   Sending prompt for: {test_title}...")
        insights = get_asta_insights(test_title, test_location, test_price)
        
        if insights:
            print("✅ Gemini Result:", json.dumps(insights, indent=2))
            
            # Check for empty values specifically
            if insights.get('investment_vibe') is None:
                print("⚠️  WARNING: API returned a dict, but values are None.")
        else:
            print("❌ Gemini returned NONE/Empty.")
            
    except Exception as e:
        print(f"❌ Gemini Module Failed with Error: {e}")

if __name__ == "__main__":
    main()
