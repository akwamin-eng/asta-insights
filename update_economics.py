import os
import requests
from dotenv import load_dotenv
from supabase import create_client

# Only load .env if it exists (local dev)
if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing Supabase credentials in environment.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
API_URL = "https://open.er-api.com/v6/latest/USD"

def run():
    print("💰 Fetching Currency Data...")
    try:
        response = requests.get(API_URL)
        data = response.json()
        ghs_rate = data['rates']['GHS']
        print(f"   Current Rate: 1 USD = {ghs_rate} GHS")

        supabase.table("economic_indicators").insert({
            "indicator_type": "USD_GHS",
            "value": ghs_rate
        }).execute()
        print("✅ Currency data saved.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
