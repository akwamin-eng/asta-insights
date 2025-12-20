import os
from dotenv import load_dotenv
from supabase import create_client

if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def run():
    print("📊 Aggregating Market Stats...")
    try:
        supabase.rpc("calculate_market_insights").execute()
        print("✅ Market stats aggregated successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
