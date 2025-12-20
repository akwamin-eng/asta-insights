# scrape_youtube.py
"""
Scrapes YouTube video metadata and transcripts using the official YouTube Data API v3.
Focuses on videos matching specific search queries related to Ghanaian real estate/market.
Integrates Google Cloud Translation API for non-English transcripts.
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
from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth
# Import Google Cloud Translation API client
from google.cloud import translate_v2 as translate

# Load environment variables
load_dotenv(dotenv_path=Path('.') / '.env')

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# --- GCS Configuration ---
GCS_BUCKET_NAME = "asta-insights-data-certain-voyager"

# --- Initialize YouTube API Client ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("Missing YOUTUBE_API_KEY in .env")

# Use Application Default Credentials (ADC) for other GCP services if needed
# This is generally handled by the environment setup (gcloud auth application-default login)
try:
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/youtube.force-ssl'])
    # If ADC is available, you can build the client with it, but API key is simpler for read-only
    # youtube = build('youtube', 'v3', credentials=credentials)
except Exception:
    # Fall back to API key if ADC fails or isn't configured for YouTube
    pass

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
print("✅ YouTube client built using API Key.")

# --- Initialize Google Cloud Translation API Client ---
# Uses Application Default Credentials (ADC)
translate_client = translate.Client()
print("✅ Google Cloud Translation client built using ADC.")

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

def fetch_youtube_transcript_api(youtube_client, video_id: str) -> str:
    """
    Fetches the transcript for a given YouTube video ID using the official YouTube Data API v3.
    Attempts to find any available caption track, downloads it, parses the text, and translates it to English.
    Uses the authenticated youtube_client.
    Returns the translated transcript text or an empty string on failure.
    """
    try:
        # 1. List available captions for the video
        caption_list_request = youtube_client.captions().list(
            part='snippet',
            videoId=video_id
        )
        caption_list_response = caption_list_request.execute()

        if not caption_list_response.get('items'):
            print(f"  ℹ️  No captions found for {video_id} via API.")
            return ""

        # 2. Find the most suitable caption track ID (prefer manual, then any available)
        caption_id = None
        original_language = None
        for item in caption_list_response['items']:
            snippet = item['snippet']
            # Prefer non-auto-generated captions first
            if not snippet.get('isAutoGenerated', False):
                caption_id = item['id']
                original_language = snippet['language']
                print(f"  📜 Found manual caption in '{original_language}' for {video_id}.")
                break

        # If no manual caption found, take the first available (auto-generated)
        if not caption_id:
            for item in caption_list_response['items']:
                 snippet = item['snippet']
                 caption_id = item['id']
                 original_language = snippet['language']
                 print(f"  📜 Found auto-generated caption in '{original_language}' for {video_id} (fallback).")
                 break

        if not caption_id:
            print(f"  ℹ️  No suitable caption track found for {video_id}.")
            return ""

        # 3. Download the caption track content (SRT format)
        srt_content = youtube_client.captions().download(
            id=caption_id,
            tfmt='srt' # or '3tts' depending on preference
        ).execute()

        # 4. Parse SRT content to extract text (SRT contains timestamps, so we need to strip them)
        # This is a simple example parsing SRT; consider using an SRT library if needed
        lines = srt_content.decode('utf-8').strip().split('\n')
        transcript_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.isdigit() and i + 2 < len(lines): # Start of an SRT entry (number)
                i += 1 # Skip the number
                # Skip timestamp line (e.g., 00:01:23,456 --> 00:01:25,789)
                i += 1
                # Collect subtitle text lines (can be multiple lines per entry)
                text_lines = []
                while i < len(lines) and lines[i].strip() != "":
                    text_lines.append(lines[i].strip())
                    i += 1
                # Add the text for this entry
                transcript_lines.append(" ".join(text_lines))
                # Skip the blank line separating entries
                if i < len(lines) and lines[i].strip() == "":
                    i += 1
            else:
                i += 1

        original_text = " ".join(transcript_lines)
        print(f"  📄 Parsed {len(transcript_lines)} entries from '{original_language}' caption for {video_id[:10]}...")

        if not original_text.strip():
            print(f"  ⚠️  Parsed caption for {video_id} is empty after processing.")
            return ""

        # 5. Translate the original text to English (if not already English)
        # --- NEW: Use Google Cloud Translation API ---
        if original_language and original_language.lower().startswith('en'):
             print(f"  ✅ Transcript is already in English for {video_id[:10]}...")
             return original_text
        else:
             print(f"  🌐 Translating transcript from '{original_language}' to English for {video_id[:10]}...")
             try:
                 # --- NEW: Detect language first (robustness) ---
                 # Although we got the language from the API, detecting it ensures the text is valid
                 # and handles edge cases where the API might report incorrectly.
                 detection_result = translate_client.detect_language(original_text)
                 detected_lang = detection_result['language']
                 print(f"    🔍 Detected language: {detected_lang} (confidence: {detection_result.get('confidence', 'N/A')})")

                 # --- NEW: Translate if needed ---
                 if detected_lang.lower().startswith('en'):
                     print(f"    ✅ Detected text is already in English for {video_id[:10]}...")
                     return original_text
                 else:
                     # Translate the text to English
                     translation_result = translate_client.translate(
                         original_text,
                         target_language='en',
                         source_language=detected_lang # Specify source for better accuracy
                     )
                     translated_text = translation_result['translatedText']
                     print(f"    ✅ Transcript translated from '{detected_lang}' to English for {video_id[:10]}...")
                     return translated_text

             except Exception as trans_e:
                 print(f"    ⚠️  Translation failed for {video_id}: {trans_e}")
                 # Optionally, return the original text if translation fails
                 # print(f"    ℹ️  Returning original language text for {video_id[:10]}... (Length: {len(original_text)})")
                 # return original_text
                 return "" # Or return empty string if translation is critical


    except HttpError as http_err:
        error_details = http_err.error_details
        reason = error_details[0].get('reason') if error_details else ''
        if reason == 'captionNotAvailable':
            print(f"  ℹ️  Transcript disabled or unavailable for {video_id}.")
        else:
             print(f"  ⚠️  HTTP error fetching/downloading transcript for {video_id}: {http_err}")
    except Exception as e:
        # --- More specific error handling ---
        error_msg = str(e)
        print(f"  ⚠️  Could not fetch/download/parse transcript for {video_id} via API: {e}")
    return "" # Return empty string on any failure

def fetch_youtube_video_details(youtube_client, video_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches detailed metadata for a list of YouTube video IDs.
    Returns a list of video detail dictionaries.
    """
    video_details_list = []
    if not video_ids:
        return video_details_list

    try:
        # Split into batches of 50 (API limit)
        batch_size = 50
        for i in range(0, len(video_ids), batch_size):
            batch_video_ids = video_ids[i:i + batch_size]
            video_details_request = youtube_client.videos().list(
                part='snippet,contentDetails,status,statistics', # Add 'contentDetails' for duration, 'status' for privacy, 'statistics' for view count if needed
                id=batch_video_ids
            )
            video_details_response = video_details_request.execute()

            for item in video_details_response.get('items', []):
                try:
                    snippet = item['snippet']
                    video_id = item['id']
                    title = snippet.get('title', '')
                    description = snippet.get('description', '')
                    publish_time = snippet.get('publishedAt', '')
                    channel_title = snippet.get('channelTitle', '')

                    # --- Fetch Transcript ---
                    full_transcript = fetch_youtube_transcript_api(youtube_client, video_id)
                    has_transcript = bool(full_transcript)

                    # --- Combine text for NLP ---
                    text_for_nlp = f"{title}. {description}"
                    if has_transcript:
                        text_for_nlp = f"{title}. {description}\n\nTranscript:\n{full_transcript}"

                    # --- Extract market terms from combined text ---
                    rule_based_terms = extract_market_terms(text_for_nlp)
                    # hotspots_and_keywords = list(set(rule_based_terms)) # Initially just rule-based

                    video_details_list.append({
                        "video_id": video_id,
                        "title": title,
                        "description": description,
                        "publish_time": publish_time,
                        "channel_title": channel_title,
                        "url": f"https://youtube.com/watch?v={video_id}",
                        "has_transcript": has_transcript,
                        "transcript_text": full_transcript, # Store for potential later use or debugging
                        "text_for_nlp": text_for_nlp, # Combined text for LLM analysis
                        "rule_based_terms": rule_based_terms, # Terms found by rule-based extraction
                        # Add other fields like duration, view count if needed from 'contentDetails' or 'statistics'
                    })
                    print(f"  📦 Fetched details for {video_id[:10]}... (Transcript: {'Yes' if has_transcript else 'No'})")

                except Exception as e_item:
                    print(f"  ⚠️ Error processing video item {item.get('id', 'unknown')}: {e_item}")
                    continue # Skip this item and continue with the rest

            # Optional: Small delay between batches to be respectful
            if i + batch_size < len(video_ids):
                 time.sleep(0.5)

    except Exception as e:
        print(f"  💥 Error fetching video details: {e}")

    return video_details_list

def fetch_youtube_insights():
    """
    Fetch YouTube videos about Ghana real estate.
    Process videos using metadata (title, description) and transcripts for NLP insights.
    Returns a DataFrame with video metadata + insights.
    """
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    if not API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY in .env")

    # Rebuild YouTube client to ensure it's fresh
    youtube_client = build('youtube', 'v3', developerKey=API_KEY)
    print("✅ YouTube client rebuilt for insights fetching.")

    # --- Fetch videos from YouTube API ---
    # --- UPDATED QUERY to include specific keywords ---
    search_query = 'Ghana real estate market trends OR "investing in Ghana" OR "building in Ghana" OR "cement price" OR "rod iron"'
    print(f"🔎 Searching YouTube for: {search_query}")
    
    video_ids = []
    request = youtube_client.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=20, # Adjust as needed
        order='date'
    )
    response = request.execute()

    for item in response['items']:
        video_id = item['id']['videoId']
        video_ids.append(video_id)
        # Optional: Print basic info during search
        # title = item['snippet']['title']
        # print(f"  Found: {title[:50]}... (ID: {video_id})")

    print(f"  📦 Found {len(video_ids)} video IDs.")

    if not video_ids:
        print("  ℹ️  No videos found for the search query.")
        return pd.DataFrame() # Return empty DataFrame

    # --- Fetch detailed metadata and transcripts for the found videos ---
    print("  📥 Fetching detailed metadata and transcripts...")
    video_details_list = fetch_youtube_video_details(youtube_client, video_ids)

    if not video_details_list:
        print("  ℹ️  No video details could be fetched.")
        return pd.DataFrame() # Return empty DataFrame

    # --- Convert to DataFrame ---
    df_videos = pd.DataFrame(video_details_list)
    print(f"  ✅ Fetched and processed {len(df_videos)} YouTube videos.")
    return df_videos

# ✅ THIS IS THE ENTRY POINT
if __name__ == "__main__":
    df = fetch_youtube_insights()
    if not df.empty:
        print("\n--- Sample Output ---")
        print(df[["video_id", "title", "has_transcript", "rule_based_terms"]].head(10))
        # Optionally, save to CSV for inspection
        # df.to_csv("youtube_insights_sample.csv", index=False)
        # print("💾 Sample output saved to youtube_insights_sample.csv")
    else:
        print("\n❌ No YouTube videos were fetched.")

