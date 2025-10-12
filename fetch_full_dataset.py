# fetch_full_dataset.py
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path('.') / '.env')

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("📥 Fetching full dataset from Supabase...")

# Fetch all properties with essential fields
response = (
    supabase.table("asta_properties")
    .select("id, price, bedrooms, bathrooms, latitude, longitude, address, zip_code, size, title")
    .not_.is_("price", "null")
    .not_.is_("latitude", "null")
    .not_.is_("longitude", "null")
    .gte("price", 100)          # exclude unrealistic prices
    .execute()
)

df = pd.DataFrame(response.data)
print(f"✅ Fetched {len(df)} properties")

# Basic inspection
print("\n📊 Dataset Overview:")
print(f"- Price range: {df['price'].min():,.0f} – {df['price'].max():,.0f}")
print(f"- Avg price: {df['price'].mean():,.0f}")
print(f"- Missing bedrooms: {df['bedrooms'].isnull().sum()}")
print(f"- Coordinate range: ({df['latitude'].min():.4f}, {df['longitude'].min():.4f}) to ({df['latitude'].max():.4f}, {df['longitude'].max():.4f})")

# Save to CSV for inspection (optional)
df.to_csv("ghana_properties_raw.csv", index=False)
print("\n💾 Saved raw data to 'ghana_properties_raw.csv'")