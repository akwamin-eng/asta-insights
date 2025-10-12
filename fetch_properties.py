# fetch_properties.py
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise EnvironmentError("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env")

supabase = create_client(url, key)
print("✅ Connected to Supabase")

try:
    # Fetch 5 properties — only using columns that exist in your schema
    response = (
        supabase.table("asta_properties")
        .select("id, price, bedrooms, bathrooms, latitude, longitude, address, zip_code, title")
        .not_.is_("price", "null")
        .not_.is_("latitude", "null")
        .not_.is_("longitude", "null")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )

    # ✅ Fixed: check if response.data exists and is non-empty
    if not response.data:
        print("⚠️ No properties found with price and coordinates.")
        exit()

    df = pd.DataFrame(response.data)
    print(f"\n✅ Fetched {len(df)} properties:\n")
    print(df[["id", "price", "bedrooms", "latitude", "longitude", "address"]].to_string(index=False))

except Exception as e:
    print(f"❌ Error fetching properties: {e}")
    exit()