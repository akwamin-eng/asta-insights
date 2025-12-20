# scrape_google_news.py
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import time
import os
import numpy as np
import re
import urllib.parse
from google.cloud import storage # For GCS upload
from dotenv import load_dotenv # For local .env

# Load environment variables
load_dotenv()

# --- Configuration ---
# Define simpler, targeted search queries for Google News.
# Run the script multiple times with different queries.
SEARCH_QUERIES = [
    "Ghana real estate market",
    "Accra property prices",
    "Ghana mortgage rates",
    "Kumasi housing development",
    "Ghana land ownership regulations",
    "Ghana inflation impact real estate", # Example combining terms
    "Ghana interest rates construction",
    # Add/remove queries as needed
]

# Base URL for Google News search results (simplified)
# {query} will be replaced. Date range is handled by iterating single days.
BASE_URL = "https://www.google.com/search?q={query}&hl=en&gl=gh&tbm=nws&as_qdr=d&safe=active" # &as_qdr=d limits to last day, might help focus

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'DNT': '1', # Do Not Track
}

# --- GCS Configuration ---
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager") # Use your bucket name
GCS_RAW_PREFIX = "raw/google_news_links"
storage_client = storage.Client() # Uses Application Default Credentials (ADC)
bucket = storage_client.bucket(GCS_BUCKET_NAME)

MAX_LINKS_PER_QUERY = 3  # Limit links fetched per query/day to be VERY respectful
DELAY_BETWEEN_QUERIES_SECONDS = 30  # Delay between different search queries
DELAY_AFTER_429_SECONDS = 60 * 15   # Delay after a 429 error (15 minutes)
DATE_FORMAT = '%Y-%m-%d' # Format used for date strings

def clean_text(text):
    """Simple text cleaning."""
    if not text:
        return ""
    return ' '.join(text.split())

def extract_article_links_from_results_page(html_content, query, search_date_str):
    """Parses Google News results page HTML to extract article links and metadata."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links_data = []

    # --- Crucial: Find the correct elements containing news results ---
    # Google's HTML is complex and changes. Look for <a> tags within news result containers.
    # Common pattern: Links often have an href starting with '/url?q='
    # Let's try a general approach first, targeting <a> tags with href.
    # Inspect the HTML structure in browser DevTools if this fails consistently.

    # Find all <a> tags. Filter them afterwards.
    link_elements = soup.find_all('a', href=True)

    count = 0
    for link_elem in link_elements:
        href = link_elem.get('href')
        # Filter for Google News redirect links
        if href.startswith('/url?q='):
            try:
                # Parse the actual URL from the Google redirect
                # Example href: /url?q=https://example.com/article&sa=...
                parsed_url = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                actual_url = query_params.get('q', [None])[0]

                if actual_url and not any(domain in actual_url for domain in ["google.com", "youtube.com", "blogger.com", "imgurl"]):
                    # Get title (often the text within the <a> tag or a child element)
                    title_elem = link_elem.find(['h3', 'div']) # Common title containers
                    title = clean_text(title_elem.get_text()) if title_elem else "No Title Found"

                    # Get snippet/description (often in a sibling or parent div)
                    # This is trickier. Look for nearby text.
                    # A common pattern is a div with class containing 's3v9rd' or similar.
                    # Let's try getting text from the parent container or siblings.
                    snippet = ""
                    parent_div = link_elem.parent
                    if parent_div:
                        # Try to get text from siblings or the parent itself that isn't the link
                        potential_texts = parent_div.find_all(string=True, recursive=False) # Direct text children of parent
                        potential_texts += [sib.get_text() for sib in parent_div.find_next_siblings()[:2]] # Text from next 2 siblings
                        snippet = ' '.join([clean_text(t) for t in potential_texts if clean_text(t)]).strip()
                        # Limit snippet length
                        snippet = snippet[:200] + "..." if len(snippet) > 200 else snippet

                    links_data.append({
                        "query": query,
                        "search_date": search_date_str,
                        "rank": count + 1,
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet,
                        # Add other potential metadata if easily extractable (source site name?)
                    })
                    count += 1
                    if count >= MAX_LINKS_PER_QUERY:
                        break
            except Exception as e_parse:
                print(f"  ⚠️  Error parsing link element: {e_parse}")
                continue # Skip this link element if parsing fails

    print(f"  📎 Extracted {len(links_data)} article links for query '{query[:30]}...' on {search_date_str}.")
    return links_data

def fetch_google_news_links_for_query(search_query, target_date_str):
    """Fetches Google News links for a single query on a specific date."""
    print(f"🔎 Searching Google News for '{search_query}' on {target_date_str}...")
    links_found = []

    # Format the URL with the query for the specific date
    # Using tbm=nws for news, as_qdr=d for last day (approximates targeting the date)
    formatted_query = search_query.replace(" ", "+")
    url = BASE_URL.format(query=formatted_query) + f"&tbs=cdr:1,cd_min:{target_date_str},cd_max:{target_date_str}"
    print(f"  📍 URL: {url[:80]}...")

    try:
        response = requests.get(url, headers=headers, timeout=20) # Increased timeout slightly
        print(f"  📡 Response Status: {response.status_code}")

        if response.status_code == 429:
            print(f"  ⏳ Hit rate limit (429). Waiting for {DELAY_AFTER_429_SECONDS / 60} minutes...")
            time.sleep(DELAY_AFTER_429_SECONDS)
            # Optionally retry once after waiting, or just skip
            print(f"  ⏭️  Skipping query '{search_query}' after 429.")
            return links_found # Return empty list
        elif response.status_code == 200:
            # Successfully fetched the results page
            links_found = extract_article_links_from_results_page(response.text, search_query, target_date_str)
        else:
            print(f"  ❌ Failed to fetch results page for '{search_query}' (Status: {response.status_code}).")
            # Log error details if possible?
    except requests.exceptions.RequestException as e_req:
        print(f"  💥 Network error fetching results page for '{search_query}': {e_req}")
    except Exception as e:
        print(f"  💥 Unexpected error fetching results page for '{search_query}': {e}")

    return links_found

def save_links_to_gcs(links_data_list, run_timestamp):
    """Saves the list of extracted links to GCS as a JSON Lines file."""
    if not links_data_list:
        print("  📝 No links to save.")
        return

    try:
        # Prepare data for saving
        output_data = "\n".join([f"{link}" for link in links_data_list]) + "\n" # JSON Lines format

        # Define GCS blob name/path
        blob_name = f"{GCS_RAW_PREFIX}/{run_timestamp}.jsonl" # Use .jsonl for JSON Lines

        # Upload to GCS
        blob = bucket.blob(blob_name)
        blob.upload_from_string(output_data, content_type='application/jsonl')
        print(f"  ✅ Saved {len(links_data_list)} links to GCS: gs://{GCS_BUCKET_NAME}/{blob_name}")

    except Exception as e_gcs:
        print(f"  ⚠️ Failed to save links to GCS: {e_gcs}")

def main():
    """Main function to iterate through queries and dates."""
    print("--- Starting Google News Link Scraper (Respectful Mode) ---")
    run_start_time = datetime.datetime.utcnow()
    run_timestamp = run_start_time.strftime("%Y%m%d_%H%M%S")
    print(f"  Run Timestamp: {run_timestamp}")

    all_links_collected = []
    total_queries = len(SEARCH_QUERIES)

    # --- Iterate through a small date range (e.g., last 3 days) ---
    # For a truly respectful approach, you might run this once a day targeting yesterday.
    # For testing/batching, a small range is okay.
    end_date_obj = run_start_time.date()
    start_date_obj = end_date_obj - datetime.timedelta(days=2) # Scrape last 3 days
    current_date_obj = start_date_obj

    while current_date_obj <= end_date_obj:
        current_date_str = current_date_obj.strftime(DATE_FORMAT)
        print(f"\n📅 Processing Date: {current_date_str}")

        for i, query in enumerate(SEARCH_QUERIES):
            print(f"\n  [{i+1}/{total_queries}] Query: {query}")
            links_for_this_query = fetch_google_news_links_for_query(query, current_date_str)
            all_links_collected.extend(links_for_this_query)

            # Delay between queries, unless it's the last one
            if i < total_queries - 1:
                print(f"  ⏱️  Waiting {DELAY_BETWEEN_QUERIES_SECONDS} seconds before next query...")
                time.sleep(DELAY_BETWEEN_QUERIES_SECONDS)

        # Move to the next date
        current_date_obj += datetime.timedelta(days=1)
        # Optional: Delay between dates if processing multiple days rapidly
        # if current_date_obj <= end_date_obj:
        #     print(f"  ⏱️  Waiting {DELAY_BETWEEN_QUERIES_SECONDS * 2} seconds before next date...")
        #     time.sleep(DELAY_BETWEEN_QUERIES_SECONDS * 2)

    print(f"\n--- Google News Link Scraper Run Completed ---")
    print(f"  Run Timestamp: {run_timestamp}")
    print(f"  Processed Dates: {start_date_obj} to {end_date_obj}")
    print(f"  Queries Used: {len(SEARCH_QUERIES)}")
    print(f"  Total Links Collected: {len(all_links_collected)}")

    # Save all collected links to GCS
    save_links_to_gcs(all_links_collected, run_timestamp)

    print("\n--- Run Finished ---")


if __name__ == "__main__":
    main()
