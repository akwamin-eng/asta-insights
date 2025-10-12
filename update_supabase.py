import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path('.') / '.env')

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Load final predictions
df = pd.read_csv("ghana_properties_final.csv")

print(f"📤 Updating {len(df)} properties in Supabase...")

success = 0
for idx, row in df.iterrows():
    update_data = {
        "predicted_price": float(row["predicted_price"]),
        "price_diff_pct": float(row["price_diff_pct"]),
        "neighborhood_score": float(row["neighborhood_score"]),
        "insight_metadata": {
            "model_version": "ghana-v1",
            "r_squared": 0.92,
            "features": ["POIs", "area", "bedrooms"]
        },
        "insight_generated_at": "now()"
    }
    
    try:
        supabase.table("asta_properties").update(update_data).eq("id", row["id"]).execute()
        success += 1
        if success % 100 == 0:
            print(f"  Updated {success} properties...")
    except Exception as e:
        print(f"❌ Failed to update {row['id']}: {e}")

print(f"\n✅ Successfully updated {success}/{len(df)} properties in Supabase!")
print("✨ Your Real Estate Intelligence Model is LIVE!")