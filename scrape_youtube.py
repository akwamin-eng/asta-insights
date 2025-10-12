#!/usr/bin/env python3
"""
Local entry point for real estate intelligence pipeline.
Saves raw and enriched data to Google Cloud Storage (GCS) for AI insights.
Computes Ghana Real Estate Index (BETA).
Based on YouTube metadata (title, description) for market sentiment.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pathlib import Path
import time
import re
from typing import List, Dict, Any # Import for type hints

# --- Vertex AI & GCS ---
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason # Import Part, FinishReason if needed
from google.cloud import storage

# --- Transcript API (Check Version) ---
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    # Check for the new API method
    if not hasattr(YouTubeTranscriptApi, 'list_transcripts'):
        print("Warning: youtube_transcript_api version might be too old. 'list_transcripts' not found. Ensure version >= 1.2.2")
    else:
        print("youtube_transcript_api v1.2.2+ detected.")
except ImportError:
    print("Warning: youtube_transcript_api not found. Install it if needed.")
    YouTubeTranscriptApi = None # Set to None if not available

# --- Supabase ---
from supabase import create_client

# --- YouTube Data API v3 ---
from googleapiclient.discovery import build

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# --- GCS Configuration ---
GCS_BUCKET_NAME = "asta-insights-data-certain-voyager"

# --- Initialize Vertex AI ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "certain-voyager-403707")
REGION = "us-central1"
GCS_BUCKET_NAME = "asta-insights-data-certain-voyager" # Your GCS bucket

vertexai.init(project=PROJECT_ID, location=REGION)
# Use a current, supported model alias
_generative_model = GenerativeModel("gemini-2.5-pro")

# --- Initialize GCS Client ---
_gcs_client = storage.Client(project=PROJECT_ID)
_gcs_bucket = _gcs_client.bucket(GCS_BUCKET_NAME)

# --- Comprehensive list of Ghanaian regions, cities, towns, and important market terms ---
GHANA_MARKET_TERMS = [
    # --- Original locations ---
    "Greater Accra", "Ashanti", "Western", "Western North", "Central", "Eastern",
    "Volta", "Oti", "Northern", "Savannah", "North East", "Upper East", "Upper West",
    "Bono", "Bono East", "Ahafo", "Accra", "Kumasi", "Tamale", "Sekondi-Takoradi",
    "Cape Coast", "Sunyani", "Ho", "Koforidua", "Wa", "Bolgatanga", "Techiman", "Tema",
    "Ashaiman", "Madina", "Dansoman", "Adenta", "Legon", "East Legon", "East Legon Hills",
    "Osu", "Cantonments", "Airport Residential", "Labadi", "Teshie", "Nungua", "Ashongman",
    "Prampram", "Kasoa", "Amasaman", "Dome", "Abeka", "Kaneshie", "Lapaz", "Awoshie",
    "Weija", "Nsawam", "Suhum", "Akosombo", "Kpong", "Bantama", "Asokwa", "Suame",
    "Tafo", "Ahwiaa", "Ejisu", "Bekwai", "Offinso", "Mampong", "Konongo", "Agogo",
    "Juaben", "Effiduase", "New Edubiase", "Obuasi", "Goaso", "Takoradi", "Sekondi",
    "Effia", "Nzema", "Axim", "Elubo", "Half Assini", "Agona", "Elmina", "Winneba",
    "Saltpond", "Mankessim", "Apam", "Anomabu", "Dunkwa", "Assin Fosu", "Twifo Praso",
    "Hemang", "Oda", "Kade", "Akim Oda", "Akim Swedru", "Nkawkaw", "Somanya", "Asamankese",
    "Atimpoku", "Hohoe", "Kpando", "Aflao", "Denu", "Keta", "Anloga", "Sogakope",
    "Akatsi", "Avegadzi", "Savelugu", "Yendi", "Gushegu", "Karaga", "Walewale", "Bimbilla",
    "Salaga", "Damongo", "Bole", "Sawla", "Tuna", "Nadowli", "Lawra", "Jirapa", "Nandom",
    "Navrongo", "Paga", "Bongo", "Zuarungu", "Fumbisi", "Sandema", "Zebilla", "Bawku",
    "Garu", "Tempane", "Nalerigu", "Gambaga", "Wulensi", "Chereponi", "Saboba", "Choggu",
    "Tolon", "Kumbungu", "Zabzugu", "Tatale", "Sanguli", "Daboya", "Mion", "Kpandai",
    "Nanumba",
    # --- NEW: Add your specific keywords ---
    "investing in Ghana",
    "building in Ghana",
    "cement price",
    "cement prices", # Plural form
    "rod iron",      # Common term
    "steel rod",     # Common alternative
    "iron rod"
    # Add any other specific locations or terms as needed
]

def extract_market_terms(text: str) -> list:
    """Extract known Ghanaian locations and important market terms from text (case-insensitive, deduplicated)."""
    if not isinstance(text, str):
        return []
    found = []
    text_lower = text.lower()
    for term in GHANA_MARKET_TERMS:
        # Simple 'in' check. Consider word boundaries for stricter matching if needed.
        if term.lower() in text_lower:
            found.append(term)
    return list(set(found)) # Remove duplicates

def fetch_youtube_transcript(video_id: str) -> str:
    """Fetches the transcript for a given YouTube video ID using the new API (if available and version is correct). Returns the transcript text or an empty string on failure."""
    if not YouTubeTranscriptApi:
        print(f"  ⚠️  YouTubeTranscriptApi library not available.")
        return ""

    try:
        # --- NEW API: List available transcripts (assuming v1.2.2+ is correctly installed) ---
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # --- Attempt to find a transcript ---
        transcript = None
        try:
            # First, try to find an English transcript (manual or auto-generated)
            transcript = transcript_list.find_transcript(['en', 'en-US'])
        except Exception:
            try:
                # If English isn't found, try to find any transcript and then translate it to English
                # Get the first available transcript
                transcript = next(iter(transcript_list))
                if transcript.is_translatable:
                    print(f"  🌐 Transcript found in '{transcript.language}' for {video_id}, translating to English...")
                    transcript = transcript.translate('en')
                else:
                    print(f"  ℹ️  Found transcript in '{transcript.language}' for {video_id}, but translation to English is not available.")
                    return ""
            except StopIteration:
                print(f"  ℹ️  No translatable transcript found for {video_id}.")
                return ""

        # --- Fetch the actual transcript data ---
        transcript_data = transcript.fetch()
        # --- Join the text parts ---
        full_transcript = " ".join([entry['text'] for entry in transcript_data])
        print(f"  📜 Transcript fetched for video ID: {video_id[:10]}...")
        return full_transcript

    except ImportError as ie:
        print(f"  ⚠️ Import error for youtube-transcript-api functions: {ie}")
    except AttributeError as ae:
        print(f"  ⚠️ AttributeError in transcript fetching (likely version mismatch): {ae}")
        print("  ℹ️  Please ensure youtube-transcript-api is version 1.2.2 or later. Run 'pip install youtube-transcript-api --upgrade'")
    except Exception as e:
        # --- More specific error handling ---
        error_msg = str(e)
        if "TranscriptsDisabled" in error_msg or "transcripts disabled" in error_msg.lower():
            print(f"  ℹ️  Transcript disabled or unavailable for {video_id}.")
        elif "NoTranscriptFound" in error_msg or "no transcript found" in error_msg.lower():
             print(f"  ℹ️  No transcript found (auto-generated/manual) for {video_id}.")
        else:
             print(f"  ⚠️  Could not fetch transcript for {video_id}: {e}")
    return "" # Return empty string on any failure

def save_transcript_to_gcs(video_id: str, transcript_text: str):
    """Saves the transcript text to a GCS bucket."""
    if not transcript_text:
        print(f"  📝 Skipping GCS save for {video_id} (no transcript).")
        return

    try:
        blob_name = f"raw/transcripts/youtube_{video_id}.txt"
        blob = _gcs_bucket.blob(blob_name)
        blob.upload_from_string(transcript_text, content_type='text/plain; charset=utf-8')
        print(f"  ✅ Transcript saved to GCS: gs://{GCS_BUCKET_NAME}/{blob_name}")
    except Exception as e:
        print(f"  ⚠️ Failed to save transcript for {video_id} to GCS: {e}")

def _robust_json_parse(json_str: str) -> Any:
    """
    Attempts to parse a JSON string, applying common fixes for LLM output errors.
    """
    # Remove potential markdown code block wrapper (```json ... ```)
    json_str = re.sub(r'^```json\s*', '', json_str, flags=re.IGNORECASE)
    json_str = re.sub(r'\s*```$', '', json_str, flags=re.IGNORECASE)

    # Attempt to parse directly first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass # Continue to try fixes

    # Fix common issues:
    # 1. Unescaped quotes inside strings (this is complex and risky, but let's try a simple replace for common cases)
    # This might not catch all, but handles some basic ones.
    # Replace unescaped double quotes inside a string value (heuristic: between : and , or } or \n, not preceded by \)
    # This regex is complex and might not be 100% safe, but it's a start.
    # A safer approach might be to use the 'json5' library if available, or 'jsonc-parser'.
    # For now, let's try a slightly safer replacement on potential string boundaries.
    # This is still heuristic and might fail for complex nested structures or comments inside strings.
    # A more robust solution might require a proper JSON repair library.
    # Let's try a simple replacement for common unescaped quotes followed by commas or colons or brackets.
    # json_str = re.sub(r'(?<=: )"(.*?)"(?=,|}|])', r'"\1"', json_str) # This is too simplistic

    # 2. Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    # 3. Ensure all property names are quoted (heuristic)
    # This is very risky and might break valid JSON if the LLM output is too far from JSON.
    # Let's try parsing again after removing trailing commas.
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # If all fixes fail, return None
    return None

def _analyze_insights_batch(video_data_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Analyzes a batch of video metadata (title, description) to generate insights.
    Attempts to get a holistic market view.
    Returns a list of insight dictionaries corresponding to the input list.
    """
    if not video_data_list:
        return []

    # Combine all titles and descriptions for a holistic view
    all_titles_descriptions = []
    for video_data in video_data_list:
        title = video_data.get("title", "")
        description = video_data.get("description", "")
        combined_text = f"Title: {title}\nDescription: {description}"
        all_titles_descriptions.append(combined_text)

    combined_text_for_llm = "\n--- Video ---\n".join(all_titles_descriptions)

    try:
        # --- Enhanced Prompt for Batch Analysis ---
        prompt = f"""
You are a real estate intelligence analyst for Ghana.
Analyze the following list of YouTube video titles and descriptions to extract overall market sentiment and key trends for the Ghanaian real estate market.
Focus on identifying common themes across the content.

For each video provided, extract ONLY the following in a valid JSON array format.
DO NOT include any other text, markdown, explanations, or formatting.
Return ONLY the JSON array starting with '[{{' and ending with '}}]'.
Ensure all JSON strings are properly escaped (e.g., use \\" for quotes inside strings).

[
  {{
    "video_id": "ID of the first video",
    "hotspots": ["list of emerging areas, e.g., 'East Legon Hills', 'Prampram', 'investing in Ghana']",
    "cost_drivers": ["list of cost factors, e.g., 'cement prices', 'land scarcity', 'rod iron']",
    "infrastructure": ["list of new projects, e.g., 'new airport', 'road expansion']",
    "market_signals": ["list of trends, e.g., 'rental yields compressing', 'demand rising', 'building in Ghana']",
    "confidence": "high|medium|low"
  }},
  {{
    "video_id": "ID of the second video",
    "hotspots": [...],
    "cost_drivers": [...],
    "infrastructure": [...],
    "market_signals": [...],
    "confidence": "high|medium|low"
  }}
  ...
]

Text: {combined_text_for_llm}
JSON Array:
"""
        # --- Robust LLM Call with Retry and Fallback ---
        max_retries = 2
        model_alias = "gemini-2.5-pro" # Primary model
        fallback_model_alias = "gemini-1.0-pro-002" # Known stable fallback

        for attempt in range(max_retries + 1):
            try:
                # Alternate between primary and fallback model on retry
                if attempt == 0:
                    current_model_alias = model_alias
                else:
                    current_model_alias = fallback_model_alias
                    print(f"  🔁 Retrying batch analysis with fallback model: {current_model_alias}")

                # Create model instance dynamically
                model_instance = GenerativeModel(current_model_alias)

                # Add a tiny delay, sometimes helps with SDK stability
                time.sleep(0.1)
                
                response = model_instance.generate_content(
                    contents=prompt,
                    generation_config={
                        "max_output_tokens": 2000, # Increase for potential batch output
                        "temperature": 0.2, # Lower temp for stricter output
                        "top_p": 0.95
                    }
                )
                # If successful, break out of the retry loop
                break
            except Exception as e:
                error_msg = str(e)
                print(f"  ⚠️  Batch LLM call failed (attempt {attempt + 1}/{max_retries + 1}) with {current_model_alias}: {error_msg}")
                if "unknown extension" in error_msg and attempt < max_retries:
                    print(f"      Retrying in 1 second with fallback model...")
                    time.sleep(1)
                elif attempt < max_retries:
                     print(f"      Retrying in 1 second...")
                     time.sleep(1)
                else:
                     print(f"  ❌  Batch LLM call failed after {max_retries + 1} attempts.")
                     # Return default insights for all videos if batch fails
                     return [{"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"} for _ in video_data_list]

        raw_text = response.text.strip()
        print(f"  🧠 Batch LLM response received (length: {len(raw_text)}).")

        # --- Robust JSON Parsing for Array ---
        result = _robust_json_parse(raw_text)

        if result is None:
            print(f"  ⚠️  Could not parse batch response as valid JSON after attempts.")
            print(f"Raw response snippet: {raw_text[:200]}...") # Log for debugging
            return [{"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"} for _ in video_data_list]

        if not isinstance(result, list):
             print(f"  ⚠️  LLM response is not a JSON array: {type(result)}")
             return [{"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"} for _ in video_data_list]


        # --- Validation and Mapping ---
        insights_list = []
        video_id_map = {vd["video_id"]: vd for vd in video_data_list} # Map video_id to original data
        for item in result:
            if not isinstance(item, dict):
                print(f"  ⚠️  Item in batch response is not a dictionary: {item}")
                insights_list.append({"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"})
                continue

            video_id = item.get("video_id")
            if not video_id or video_id not in video_id_map:
                print(f"  ⚠️  Item in batch response has invalid or missing video_id: {item}")
                # Append a default insight if ID doesn't match
                insights_list.append({"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"})
                continue

            # Validate keys and types for this item
            required_keys = ["hotspots", "cost_drivers", "infrastructure", "market_signals", "confidence"]
            if not all(key in item for key in required_keys):
                 print(f"  ⚠️  Item for {video_id} missing required keys: {item}")
                 insights_list.append({"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"})
                 continue

            # Ensure list fields are lists and contain strings, confidence is valid
            for key in ["hotspots", "cost_drivers", "infrastructure", "market_signals"]:
                 if not isinstance(item.get(key, []), list):
                      item[key] = [str(item[key])] if item.get(key) else []
                 else:
                      item[key] = [str(sub_item) for sub_item in item[key]]

            conf = item.get("confidence", "low").lower()
            if conf not in ["high", "medium", "low"]:
                 item["confidence"] = "low"
            else:
                 item["confidence"] = conf

            insights_list.append({
                "hotspots": item["hotspots"],
                "cost_drivers": item["cost_drivers"],
                "infrastructure": item["infrastructure"],
                "market_signals": item["market_signals"],
                "confidence": item["confidence"]
            })

        # Ensure the final list matches the input length
        if len(insights_list) != len(video_data_list):
             print(f"  ⚠️  Batch analysis returned {len(insights_list)} insights, but {len(video_data_list)} were expected. Padding with defaults.")
             while len(insights_list) < len(video_data_list):
                  insights_list.append({"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"})

        return insights_list

    except Exception as e:
        print(f"💥 Error in _analyze_insights_batch: {e}")
        # import traceback
        # traceback.print_exc()
        # Return defaults on any failure
        return [{"hotspots": [], "cost_drivers": [], "infrastructure": [], "market_signals": [], "confidence": "low"} for _ in video_data_list]


def compute_index():
    """
    Compute daily Ghana Real Estate Index by city.
    Stores median predicted_price per city for the last 30 days.
    """
    try:
        # Recreate client inside function as it's a separate task
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY for index computation")
        supabase = create_client(url, key)

        # --- 1. Fetch last 30 days of insight history ---
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        history_response = supabase.table("asta_property_insight_history") \
            .select("property_id, predicted_price, insight_generated_at") \
            .gte("insight_generated_at", thirty_days_ago) \
            .execute()

        # --- 2. Check if data exists ---
        if not history_response.data: # <-- CORRECTED: Check .data
            print("⚠️ No recent insight history found for index calculation.")
            return

        history_df = pd.DataFrame(history_response.data)
        print(f"📊 Fetched {len(history_df)} recent insight records for index.")

        # --- 3. Get property addresses ---
        property_ids = history_df['property_id'].unique().tolist()
        if not property_ids:
             print("⚠️ No property IDs found in insight history.")
             return

        properties_response = supabase.table("asta_properties") \
            .select("id, address") \
            .in_("id", property_ids) \
            .execute()

        if not properties_response.data: # <-- CORRECTED: Check .data
            print("⚠️ No property addresses found.")
            return

        properties_df = pd.DataFrame(properties_response.data)
        properties_df.rename(columns={"id": "property_id"}, inplace=True)

        # --- 4. Merge dataframes ---
        merged_df = history_df.merge(properties_df, on="property_id", how="inner")
        if merged_df.empty:
            print("⚠️ Merged data is empty for index calculation.")
            return

        # --- 5. Extract city from address ---
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

        # --- 6. Group by city and compute median predicted_price ---
        index_data = []
        for city, group in merged_df.groupby('city'):
            if len(group) < 3: # Require minimum data points
                continue
            median_price = group['predicted_price'].median()
            index_data.append({
                "region": "Ghana",
                "city": city,
                "median_predicted_price": float(median_price),
                "month": datetime.now(timezone.utc).strftime('%Y-%m-01') # First of current month
            })

        if not index_data: # <-- CORRECTED: Check the list itself
            print("⚠️ No valid city groups found for index (insufficient data per city).")
            return

        # --- 7. Insert into ghana_real_estate_index table ---
        supabase.table("ghana_real_estate_index").upsert(index_data).execute()
        print(f"✅ Computed and saved real estate index for {len(index_data)} cities.")

    except Exception as e:
        print(f"💥 Error in compute_index: {e}")
        # import traceback
        # traceback.print_exc()

def fetch_youtube_insights():
    """
    Fetch YouTube videos about Ghana real estate.
    Process videos using metadata (title, description) for NLP insights.
    Returns a DataFrame with video metadata + insights.
    """
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    if not API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY in .env")

    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # --- Fetch videos from YouTube API ---
    # --- UPDATED QUERY to include specific keywords ---
    search_query = 'Ghana real estate market trends OR "investing in Ghana" OR "building in Ghana" OR "cement price" OR "rod iron"'
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=20, # Adjust as needed
        order='date'
    )
    response = request.execute()

    videos_metadata = [] # Store metadata for batch processing
    processed_count = 0

    for item in response['items']:
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        description = item['snippet']['description']
        publish_time = item['snippet']['publishedAt']
        url = f"https://youtube.com/watch?v={video_id}"

        print(f"\n🎬 Processing: {title[:50]}... (ID: {video_id})")

        # --- Fetch Transcript (Attempt, but proceed with metadata regardless) ---
        full_transcript = fetch_youtube_transcript(video_id)
        has_transcript = bool(full_transcript)

        if has_transcript:
            processed_count += 1
            print(f"  📜 Transcript found, saved to GCS. Analyzing with transcript.")
            # Save transcript to GCS (optional, depends on your pipeline)
            save_transcript_to_gcs(video_id, full_transcript)
            # Use full text (transcript + metadata) for this specific video's text_for_nlp later if needed
            # For now, we'll stick to metadata for the batch analysis
        else:
            print(f"  ℹ️  No transcript available. Analyzing metadata only.")

        # --- Collect metadata for batch analysis ---
        videos_metadata.append({
            "video_id": video_id,
            "title": title,
            "description": description,
            "publish_time": publish_time,
            "url": url,
            "insight_source": "metadata_only" if not has_transcript else "transcript_available"
        })

        # --- Optional: Small delay to be respectful to APIs ---
        time.sleep(0.1)

    print(f"\n📊 Collected metadata for {len(videos_metadata)} videos. Starting batch analysis...")

    # --- Batch Analysis ---
    batch_insights = _analyze_insights_batch(videos_metadata)

    # --- Save Insights to Supabase and prepare DataFrame ---
    videos_with_insights = []
    for meta, insights in zip(videos_metadata, batch_insights):
        video_id = meta["video_id"]
        title = meta["title"]
        description = meta["description"]
        publish_time = meta["publish_time"]
        url = meta["url"]
        insight_source = meta["insight_source"]

        # --- Merge LLM insights with rule-based term extraction ---
        text_for_term_extraction = f"{title}. {description}" # Use metadata for term extraction
        rule_based_terms = extract_market_terms(text_for_term_extraction)
        combined_hotspots_and_terms = list(set(insights["hotspots"] + rule_based_terms))

        # --- 4. Save Insights to Supabase ---
        try:
            supabase.table("ghana_market_insights").insert({
                "video_id": video_id,
                "title": title,
                "hotspots": combined_hotspots_and_terms, # This now includes locations and keywords
                "cost_drivers": insights["cost_drivers"],
                "infrastructure": insights["infrastructure"],
                "market_signals": insights["market_signals"],
                "confidence": insights["confidence"],
                "publish_time": publish_time,
                "insight_source": insight_source # Track data source
            }).execute()
            print(f"  ✅ Insights saved for {video_id[:10]}... (Source: {insight_source})")
        except Exception as e:
            print(f"  ⚠️ Failed to save insights for {video_id}: {e}")

        # --- 5. Collect data for DataFrame ---
        videos_with_insights.append({
            "video_id": video_id,
            "title": title,
            "description": description,
            "publish_time": publish_time,
            "url": url,
            "insights": insights,
            "insight_source": insight_source
        })

    # --- 6. Compute Ghana Real Estate Index ---
    print("\n📈 Computing Ghana Real Estate Index (BETA)...")
    compute_index()

    print(f"\n✅ Fetched and processed {len(videos_with_insights)} YouTube videos (metadata only).")
    if processed_count > 0:
        print(f"  - {processed_count} had transcripts (saved to GCS).")
    return pd.DataFrame(videos_with_insights)

# ✅ THIS IS THE ENTRY POINT
if __name__ == "__main__":
    df = fetch_youtube_insights()
    print("\n--- Sample Output ---")
    print(df[["video_id", "title", "insight_source", "insights"]].head(10))
