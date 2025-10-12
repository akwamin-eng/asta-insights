#!/usr/bin/env python3
"""
Local entry point for real estate intelligence pipeline.
Saves raw and enriched data to Google Cloud Storage (GCS) for AI insights.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pathlib import Path
from google.cloud import storage
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# GCS Configuration
GCS_BUCKET_NAME = "asta-insights-data-certain-voyager"

def upload_to_gcs(bucket_name, data, destination_blob_name):
    """Upload JSON-serializable data to GCS as JSON."""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(
            json.dumps(data, default=str, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8"
        )
        print(f"✅ Uploaded to gs://{bucket_name}/{destination_blob_name}")
    except Exception as e:
        print(f"⚠️ Failed to upload to GCS: {e}")

def compute_index():
    """
    Compute daily Ghana Real Estate Index by city.
    Stores median predicted_price per city for the last 30 days.
    """
    load_dotenv(dotenv_path=Path('.') / '.env')
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    try:
        # Get last 30 days of insight history
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        history_response = supabase.table("asta_property_insight_history") \
            .select("property_id, predicted_price, insight_generated_at") \
            .gte("insight_generated_at", thirty_days_ago) \
            .execute()
        
        if not history_response.data:
            print("⚠️ No recent insight history found for index calculation.")
            return

        history_df = pd.DataFrame(history_response.data)

        # Get property addresses
        property_ids = history_df['property_id'].unique().tolist()
        properties_response = supabase.table("asta_properties") \
            .select("id, address") \
            .in_("id", property_ids) \
            .execute()
        
        if not properties_response.data:
            print("⚠️ No property addresses found.")
            return

        properties_df = pd.DataFrame(properties_response.data)
        properties_df.rename(columns={"id": "property_id"}, inplace=True)

        # Merge
        merged_df = history_df.merge(properties_df, on="property_id", how="inner")
        if merged_df.empty:
            print("⚠️ Merged data is empty.")
            return

        # Extract city from address
        def extract_city(address):
            if not isinstance(address, str):
                return "Unknown"
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if len(parts) >= 2:
                return parts[-1].title()
            elif len(parts) == 1:
                return parts[0].title()
            return "Unknown"

        merged_df['city'] = merged_df['address'].apply(extract_city)

        # Group by city and compute median predicted_price
        index_data = []
        for city, group in merged_df.groupby('city'):
            if len(group) < 3:  # Require min 3 properties
                continue
            median_price = float(group['predicted_price'].median())
            if not pd.isfinite(median_price):
                continue
            index_data.append({
                "region": "Ghana",
                "city": city,
                "median_predicted_price": median_price,
                "month": datetime.now(timezone.utc).strftime('%Y-%m-01')
            })

        if not index_data:
            print("⚠️ No valid city groups with sufficient data.")
            return

        # Insert into ghana_real_estate_index
        supabase.table("ghana_real_estate_index").upsert(index_data).execute()
        print(f"✅ Computed real estate index for {len(index_data)} cities")

    except Exception as e:
        print(f"💥 Error computing index: {e}")

def main():
    try:
        print("🚀 Starting real estate intelligence pipeline (local mode)...")
        
        # Import your core logic
        from scrape_ghana_listings import scrape_all
        from scrape_youtube import fetch_youtube_insights
        from train_and_update import run_full_pipeline
        
        # Generate timestamp for versioning
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # === 1. Scrape Ghana Listings ===
        listings_df = scrape_all()
        print(f"✅ Scraped {len(listings_df)} Ghana listings")
        
        if not listings_df.empty:
            listings_json = listings_df.to_dict(orient="records")
            upload_to_gcs(
                GCS_BUCKET_NAME,
                listings_json,
                f"raw/listings_{timestamp}.json"
            )
        
        # === 2. Scrape YouTube Insights ===
        youtube_df = fetch_youtube_insights()
        print(f"✅ Fetched {len(youtube_df)} YouTube videos")
        
        if not youtube_df.empty:
            youtube_json = youtube_df.to_dict(orient="records")
            upload_to_gcs(
                GCS_BUCKET_NAME,
                youtube_json,
                f"raw/youtube_{timestamp}.json"
            )
        
        # === 3. Run Full Pipeline & Get Enriched Data ===
        enriched_df = run_full_pipeline(scraped_df=listings_df)
        
        if enriched_df is not None and not enriched_df.empty:
            # Select key insight columns
            insight_cols = [
                "id", "price", "predicted_price", "price_diff_pct",
                "neighborhood_score", "latitude", "longitude", "address"
            ]
            cols_to_save = [c for c in insight_cols if c in enriched_df.columns]
            insights_df = enriched_df[cols_to_save].copy()
            
            insights_json = insights_df.to_dict(orient="records")
            upload_to_gcs(
                GCS_BUCKET_NAME,
                insights_json,
                f"enriched/insights_{timestamp}.json"
            )
        
        # === 4. Compute Ghana Real Estate Index (BETA) ===
        compute_index()
        
        print("✅ Pipeline completed successfully with GCS backup!")
        
    except Exception as e:
        print(f"💥 Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()