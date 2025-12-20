import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment
if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_status():
    print("🔍 Checking Heatmap Data Status...")
    
    try:
        # 1. Check for locations with coordinates (Corrected Syntax)
        res_ready = supabase.table("market_insights") \
            .select("location", count="exact") \
            .not_("latitude", "is", "null") \
            .execute()
        
        # 2. Check for locations MISSING coordinates (Corrected Syntax)
        res_missing = supabase.table("market_insights") \
            .select("location", count="exact") \
            .is_("latitude", "null") \
            .execute()

        # The count is accessed via the 'count' property of the response object
        ready_count = res_ready.count if res_ready.count is not None else 0
        missing_count = res_missing.count if res_missing.count is not None else 0
        total = ready_count + missing_count

        print("-" * 40)
        print(f"✅ Ready for Map:   {ready_count}")
        print(f"❌ Missing Coords:  {missing_count}")
        print(f"📊 Coverage:        {(ready_count/total)*100:.1f}%" if total > 0 else "📊 Coverage: 0%")
        print("-" * 40)

        if missing_count > 0:
            print("\n📍 Top neighborhoods that need geocoding:")
            # Use .data to see the actual rows
            for item in res_missing.data[:10]:
                print(f"   - {item['location']}")
        else:
            print("\n🎉 Excellent! Your Heatmap is 100% geographically mapped.")

    except Exception as e:
        print(f"❌ Error during check: {e}")

if __name__ == "__main__":
    check_status()
