import os
import requests
import sys
from supabase import create_client, Client

# --- Configuration ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY")
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"

def update_rates():
    print("💱 [Currency Sync] Starting...")
    
    if not API_KEY:
        print("❌ Error: EXCHANGE_RATE_API_KEY is missing.")
        sys.exit(1)

    # 1. Fetch from ExchangeRate-API
    try:
        response = requests.get(BASE_URL)
        data = response.json()
        
        if data["result"] != "success":
            raise Exception(f"API Error: {data.get('error-type', 'Unknown error')}")
            
        ghs_rate = data["conversion_rates"]["GHS"]
        print(f"✅ Rate Acquired: 1 USD = {ghs_rate} GHS")
        
        # 2. Update Supabase
        # We store this in 'system_config' so the frontend/backend can read it anytime
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        payload = {
            "key": "ghs_usd_rate",
            "value": str(ghs_rate), # Storing as string to preserve decimal precision if needed
            "description": "Live USD to GHS exchange rate",
            "last_updated": "now()"
        }

        # Upsert: Update if exists, Insert if new
        data = supabase.table("system_config").upsert(payload, on_conflict="key").execute()
        
        print("💾 Database Updated: 'system_config' table synced.")
        
    except Exception as e:
        print(f"❌ Failed to update currency: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_rates()
 # Force git registration
