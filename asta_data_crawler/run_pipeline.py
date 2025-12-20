# run_pipeline.py
"""
Orchestrates the full ASTA data pipeline, including YouTube insights processing.
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import time
from typing import List, Dict, Any

# --- Import ASTA modules ---
# Import the central config
from config.config import config

# Import data source modules
from scrape_youtube import fetch_youtube_insights # NEW: Import YouTube scraper

# Import storage modules
from storage.supabase_connector import SupabaseConnector

# Import processing modules
from processing.llm_tasks.analyze_youtube_insights import analyze_youtube_insights_batch # NEW: Import LLM analysis function

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# --- GCS Configuration (if needed for archival) ---
GCS_BUCKET_NAME = config.GCS_BUCKET_NAME # Use from central config

def save_youtube_insights_to_gcs(df: pd.DataFrame, timestamp: str):
    """Saves the YouTube insights DataFrame to GCS as JSON."""
    # TODO: Implement GCS upload logic here if needed for archival
    # Use google.cloud.storage.Client
    # blob_name = f"raw/youtube_insights/youtube_insights_{timestamp}.json"
    # Convert DataFrame to JSON string and upload
    # blob.upload_from_string(df.to_json(orient='records'), content_type='application/json')
    print(f"  📦 YouTube insights saved to GCS (placeholder).")

def main():
    """Main function to run the full pipeline."""
    start_time = datetime.now(timezone.utc)
    timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
    print(f"🚀 Starting ASTA Data Pipeline Run ({timestamp_str})...")

    try:
        # --- 1. Fetch YouTube Insights ---
        print("\n--- Step 1: Fetching YouTube Insights ---")
        df_youtube = fetch_youtube_insights() # This now uses the official API and includes transcripts + translation

        if df_youtube.empty:
            print("  ⚠️  No YouTube insights fetched. Skipping further YouTube processing.")
        else:
            print(f"  ✅ Fetched {len(df_youtube)} YouTube videos with metadata/transcripts.")
            
            # --- 2. Save YouTube Insights to GCS (Optional Archival) ---
            print("\n--- Step 2: Saving YouTube Insights to GCS ---")
            save_youtube_insights_to_gcs(df_youtube, timestamp_str)

            # --- 3. Analyze YouTube Insights with Groq ---
            print("\n--- Step 3: Analyzing YouTube Insights with Groq ---")
            # Convert DataFrame rows to list of dictionaries for analysis
            video_data_list = df_youtube.to_dict(orient='records')
            
            # Call the LLM analysis function
            analyzed_insights_list = analyze_youtube_insights_batch(video_data_list)
            
            # Merge LLM insights with rule-based terms
            final_insights_list = []
            for video_data, llm_insights in zip(video_data_list, analyzed_insights_list):
                # Combine rule-based terms with LLM-extracted hotspots
                combined_hotspots = list(set(video_data.get("rule_based_terms", []) + llm_insights.get("hotspots", [])))
                
                final_insight = {
                    "video_id": video_data["video_id"],
                    "title": video_data["title"],
                    "hotspots": combined_hotspots,
                    "cost_drivers": llm_insights.get("cost_drivers", []),
                    "infrastructure": llm_insights.get("infrastructure", []),
                    "market_signals": llm_insights.get("market_signals", []),
                    "confidence": llm_insights.get("confidence", "low"),
                    "publish_time": video_data["publish_time"],
                    "insight_source": "youtube_transcript" if video_data["has_transcript"] else "youtube_metadata"
                }
                final_insights_list.append(final_insight)

            # --- 4. Save Analyzed Insights to Supabase ---
            print("\n--- Step 4: Saving Analyzed Insights to Supabase ---")
            supabase_conn = SupabaseConnector()
            inserted_count = supabase_conn.insert_youtube_insights(final_insights_list) # You'll need to implement this method in SupabaseConnector
            print(f"  ✅ Saved {inserted_count} YouTube insights to Supabase.")

        # --- 5. (Existing) Compute Ghana Real Estate Index ---
        print("\n--- Step 5: Computing Ghana Real Estate Index (BETA) ---")
        from train_and_update import compute_index # Import the compute_index function
        compute_index() # This should now work if historical data exists

        end_time = datetime.now(timezone.utc)
        duration = end_time - start_time
        print(f"\n✅ ASTA Data Pipeline Run ({timestamp_str}) completed successfully!")
        print(f"  Duration: {duration}")
        if not df_youtube.empty:
            print(f"  YouTube Insights: Fetched {len(df_youtube)}, Analyzed {len(final_insights_list)}, Saved {inserted_count}")

    except Exception as e:
        error_time = datetime.now(timezone.utc)
        print(f"\n💥 ASTA Data Pipeline Run ({timestamp_str}) failed: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Failed: {str(e)}", 500

    return "✅ Pipeline completed!", 200

if __name__ == "__main__":
    # Run the main function
    result_message, status_code = main()
    print(result_message)
    sys.exit(0 if status_code == 200 else 1)

