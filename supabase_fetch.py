# supabase_fetch.py
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def connect_to_supabase() -> Client:
    """Initialize and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise EnvironmentError(
            "Missing SUPABASE_URL or SUPABASE_KEY in environment variables. "
            "Please set them in your .env file."
        )
    
    return create_client(url, key)

def fetch_listings_table(supabase: Client) -> pd.DataFrame:
    """Fetch all records from the 'listings' table in Supabase."""
    try:
        response = supabase.table("listings").select("*").execute()
        
        if not response.data:
            print("Warning: No data returned from 'listings' table.")
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        print(f"✅ Successfully fetched {len(df)} listings from Supabase.")
        return df

    except Exception as e:
        print(f"❌ Error fetching data from Supabase: {e}")
        raise

def main():
    try:
        supabase = connect_to_supabase()
        df_listings = fetch_listings_table(supabase)
        
        # Optional: Display first few rows
        if not df_listings.empty:
            print("\nSample data:")
            print(df_listings.head())
        
        # You can now use df_listings for cleaning, modeling, etc.
        return df_listings

    except Exception as e:
        print(f"💥 Fatal error: {e}")
        return None

if __name__ == "__main__":
    df = main()