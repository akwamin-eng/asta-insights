import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Free Exchange Rate API (No key needed for basic usage)
API_URL = "https://open.er-api.com/v6/latest/USD"

def run():
    print("💰 Fetching Currency Data...")
    try:
        response = requests.get(API_URL)
        data = response.json()
        
        ghs_rate = data['rates']['GHS']
        print(f"   Current Rate: 1 USD = {ghs_rate} GHS")

        # Insert into Database
        payload = {
            "indicator_type": "USD_GHS",
            "value": ghs_rate
        }
        supabase.table("economic_indicators").insert(payload).execute()
        print("✅ Currency data saved.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
