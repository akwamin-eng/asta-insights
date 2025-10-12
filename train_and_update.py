# train_and_update.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env ONCE at module level
load_dotenv(dotenv_path=Path('.') / '.env')

# Import other modules
import pandas as pd
import numpy as np
from supabase import create_client
import xgboost as xgb

def fetch_supabase_data():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    
    supabase = create_client(url, key)
    
    response = (
        supabase.table("asta_properties")
        .select("id, price, bedrooms, bathrooms, latitude, longitude, address, size")
        .not_.is_("price", "null")
        .not_.is_("latitude", "null")
        .not_.is_("longitude", "null")
        .gte("price", 1000)
        .execute()
    )
    return pd.DataFrame(response.data)

def parse_size_to_sqm(size_val):
    try:
        if pd.isna(size_val):
            return np.nan
        value = float(size_val)
        return value * 0.092903
    except (ValueError, TypeError):
        return np.nan

def generate_realistic_prices(df):
    def get_location_factor(address):
        if not isinstance(address, str):
            return 1.0
        addr = address.lower()
        if any(x in addr for x in ["legon", "osu", "cantonments"]):
            return 1.8
        elif "accra" in addr:
            return 1.5
        elif any(x in addr for x in ["takoradi", "kumasi"]):
            return 1.2
        return 1.0

    df = df.copy()
    df['location_factor'] = df['address'].apply(get_location_factor)
    df['area_sqm'] = df['size'].apply(parse_size_to_sqm)
    df = df[df['area_sqm'] >= 10].copy()
    
    base_price = (
        df['area_sqm'] * 800 +
        df['bedrooms'].fillna(2) * 5000 +
        df['bathrooms'].fillna(1) * 3000
    )
    df['price'] = (base_price * df['location_factor']).round()
    return df

def save_insights_to_history(supabase_df):
    """Save predictions to asta_property_insight_history."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    
    supabase = create_client(url, key)
    
    history_records = []
    for _, row in supabase_df.iterrows():
        history_records.append({
            "property_id": str(row["id"]),
            "predicted_price": float(row["predicted_price"]),
            "price_diff_pct": float(row["price_diff_pct"]),
            "neighborhood_score": float(row["neighborhood_score"]),
            "insight_generated_at": "now()"
        })
    
    if history_records:
        supabase.table("asta_property_insight_history").upsert(history_records).execute()
        print(f"✅ Saved {len(history_records)} records to insight history")

def run_full_pipeline(scraped_df=None):
    """
    Train model and update Supabase with insights.
    Returns enriched DataFrame for archival.
    """
    # 1. Fetch data
    supabase_df = fetch_supabase_data()
    if supabase_df.empty:
        raise ValueError("No data in Supabase")

    # 2. Generate realistic prices
    supabase_df = generate_realistic_prices(supabase_df)

    # 3. Combine with scraped data
    if scraped_df is not None and not scraped_df.empty:
        combined_df = pd.concat([supabase_df, scraped_df], ignore_index=True)
    else:
        combined_df = supabase_df

    # 4. Prepare features
    combined_df['area_sqm'] = combined_df['area_sqm'].fillna(combined_df['area_sqm'].median())
    combined_df['bedrooms'] = combined_df['bedrooms'].fillna(2)
    combined_df['bathrooms'] = combined_df['bathrooms'].fillna(1)

    features = ['bedrooms', 'bathrooms', 'area_sqm', 'latitude', 'longitude']
    X = combined_df[features].fillna(0)
    y = np.log1p(combined_df['price'])

    # 5. Train model
    model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42)
    model.fit(X, y)

    # 6. Predict on Supabase data only
    X_supabase = supabase_df[features].fillna(0)
    supabase_df['predicted_price'] = np.expm1(model.predict(X_supabase))

    # 7. Compute price_diff_pct safely
    supabase_df['price_diff_pct'] = np.where(
        supabase_df['price'] != 0,
        (supabase_df['predicted_price'] - supabase_df['price']) / supabase_df['price'],
        0.0
    )

    # 8. Compute neighborhood score (0–100)
    supabase_df['neighborhood_score'] = (
        np.clip(supabase_df['bedrooms'] / 5, 0, 1) * 30 +
        np.clip(supabase_df['area_sqm'] / 200, 0, 1) * 40 +
        np.clip(supabase_df['price_diff_pct'] + 1, 0, 1) * 30
    ).round(1)

    # 9. Update Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    
    supabase = create_client(url, key)

    updated = 0
    for _, row in supabase_df.iterrows():
        update_data = {
            "predicted_price": float(row["predicted_price"]),
            "price_diff_pct": float(row["price_diff_pct"]),
            "neighborhood_score": float(row["neighborhood_score"]),
            "insight_generated_at": "now()"
        }
        try:
            supabase.table("asta_properties").update(update_data).eq("id", row["id"]).execute()
            updated += 1
        except Exception as e:
            print(f"⚠️ Failed to update {row['id']}: {e}")

    print(f"✅ Updated {updated} properties in Supabase")

    # 10. Save to historical table for time-series analysis
    save_insights_to_history(supabase_df)

    # 11. Return for GCS archival
    return supabase_df