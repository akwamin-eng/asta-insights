import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def save_listing_safely(item):
    """
    Manually handles the Upsert logic to avoid 
    'UPDATE requires a WHERE clause' errors.
    """
    target_url = item["url"]
    
    print(f"   🔍 Checking if '{target_url}' exists...")
    
    # 1. Try to find the record
    try:
        response = supabase.table("market_listings").select("url").eq("url", target_url).execute()
        exists = len(response.data) > 0
    except Exception as e:
        print(f"   ⚠️ Read Error: {e}")
        return False

    # 2. Update or Insert based on finding
    try:
        if exists:
            print("   🔄 Found existing record. Updating...")
            # We don't update the 'id' or 'url' typically
            update_data = {k:v for k,v in item.items() if k not in ['id', 'url']}
            supabase.table("market_listings").update(update_data).eq("url", target_url).execute()
        else:
            print("   ➕ New record. Inserting...")
            supabase.table("market_listings").insert(item).execute()
            
        return True
    except Exception as e:
        print(f"   ❌ Write Error: {e}")
        return False

def main():
    print("🛠️  DEBUG: Attempting robust write to Supabase...")

    # Generate a random ID to ensure we satisfy any UUID constraints
    # But keep a fixed 'url' to test the update logic
    
    test_item = {
        # Generate a new ID if inserting, but it will be ignored on update
        "id": str(uuid.uuid4()), 
        "url": "debug_test_123",
        "title": "Debug Test Property (Manual Logic)",
        "price": 125000,
        "location": "Test Location",
        "source": "manual_debug_script",
        "insight_cache": {"investment_vibe": "Manual Check Success"},
        "location_intel": {"verdict": "Test Zone", "tags": ["Debug", "Manual"]},
        "insight_last_updated": datetime.now().isoformat(),
        "last_seen_at": datetime.now().isoformat(),
        "raw_data": {"note": "This bypasses the upsert error"}
    }

    success = save_listing_safely(test_item)
    
    if success:
        print("\n✅ SUCCESS! Record saved safely.")
    else:
        print("\n❌ FAILURE! Could not save record.")

if __name__ == "__main__":
    main()
