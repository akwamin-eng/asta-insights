import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def run():
    print("📊 Aggregating Market Stats...")
    
    # 1. Fetch all unique locations
    # Note: In a huge DB, we'd do this via SQL, but for 20k rows Python is fine for prototyping
    # We will use a SQL RPC function for efficiency
    
    try:
        # We need a SQL function to do the heavy lifting
        # (See the SQL block below this script in the instructions)
        response = supabase.rpc("calculate_market_insights").execute()
        print("✅ Market stats aggregated successfully.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
