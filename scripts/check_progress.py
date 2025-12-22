import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

def main():
    print("🔍 Verifying previous progress...")
    
    # Check count of enriched items
    try:
        # We verify by checking if 'insight_cache' is not null (meaning AI processed it)
        res = supabase.table("market_listings").select("title", count="exact").not_.is_("insight_cache", "null").execute()
        count = res.count
        
        print(f"✅ Database currently holds {count} enriched properties.")
        
        if count and count > 0:
            print("\n--- Latest 5 Entries ---")
            latest = supabase.table("market_listings").select("title, location, insight_last_updated").order("insight_last_updated", desc=True).limit(5).execute()
            for item in latest.data:
                print(f"   🏠 {item['title'][:40]}... (Saved at: {item['insight_last_updated']})")
        else:
            print("⚠️ No enriched data found. The previous run might have failed before saving.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
