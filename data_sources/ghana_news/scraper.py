# scrape_news_sentiment.py
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import datetime
import pandas as pd
import time
import os
import numpy as np
from textblob import TextBlob # Import TextBlob for sentiment analysis
import re # Import re for cleaning text

# --- Configuration ---
# Define the search query for Google News.
# Using 'OR' within the query string for Google News search
# Focus on Ghanaian real estate, economy, finance, and related sectors
SEARCH_QUERY = "Ghana real estate OR Ghana property market OR Ghana housing OR Accra property OR Kumasi property OR Ghana economy OR Ghana inflation OR Ghana interest rates OR Ghana construction OR Ghana mortgage OR Ghana land ownership OR Ghana housing policy OR Ghana rental market OR Ghana property investment OR Ghana home affordability"
# Base URL for Google News search results
# {query}, {min_date}, {max_date} will be filled in later
BASE_URL = "https://www.google.com/search?q={query}&hl=en&gl=gh&as_drrb=b&tbas=0&tbs=cdr:1,cd_min:{min_date},cd_max:{max_date},sbd:1&tbm=nws&sxsrf=ACYBGNRfmviSo9arK1e_P_YIl5wsskZBPw:1574225634362&source=lnt&sa=X&ved=0ahUKEwj4wu29__flAhWV9Z4KHaKJAGcQpwUIIA&biw=1685&bih=863&dpr=1.1"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36', # Updated to reflect a Mac user agent
    'Content-Type': 'text/html',
}

MAX_ARTICLES_PER_DAY = 5  # Limit articles fetched per day to be respectful
DATE_FORMAT = '%m/%d/%Y' # Format used for date strings in the URL
# Define columns for the output CSV
NEWS_COLS = ['date', 'search_query', 'status_code', 'url_fetched'] + \
            [f'article_{i}_url' for i in range(1, MAX_ARTICLES_PER_DAY+1)] + \
            [f'article_{i}_title' for i in range(1, MAX_ARTICLES_PER_DAY+1)] + \
            [f'article_{i}_summary' for i in range(1, MAX_ARTICLES_PER_DAY+1)] + \
            [f'article_{i}_publish_date' for i in range(1, MAX_ARTICLES_PER_DAY+1)] + \
            [f'article_{i}_sentiment_polarity' for i in range(1, MAX_ARTICLES_PER_DAY+1)] + \
            [f'article_{i}_sentiment_subjectivity' for i in range(1, MAX_ARTICLES_PER_DAY+1)] + \
            [f'article_{i}_sentiment_label' for i in range(1, MAX_ARTICLES_PER_DAY+1)]

def clean_text(text):
    """Simple text cleaning to remove extra whitespace and newlines."""
    if not text:
        return ""
    # Remove extra whitespace/newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_sentiment(text):
    """Analyze sentiment using TextBlob. Returns polarity, subjectivity, and a label."""
    if not text:
        return 0.0, 0.0, "neutral"
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity # Ranges from -1 (negative) to 1 (positive)
    subjectivity = blob.sentiment.subjectivity # Ranges from 0 (objective) to 1 (subjective)
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return polarity, subjectivity, label

def run_google_news_scrapper(search_query, min_date, max_date, output_file):
    """Scrapes Google News for a given query and date range, analyzes sentiment, and saves results."""
    print(f"Scraping Google News for '{search_query}' on {min_date}...")
    news_data_dict = {}
    news_data_dict['date'] = min_date
    news_data_dict['search_query'] = search_query

    # Format the URL with the query and dates
    url = BASE_URL.format(query=search_query.replace(" ", "+"), min_date=min_date, max_date=max_date)
    news_data_dict['url_fetched'] = url
    print(f"  Generated URL: {url[:100]}...") # Print part of the URL for inspection

    try:
        response = requests.get(url, headers=headers)
        news_data_dict['status_code'] = response.status_code
        print(f"  Response Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"  ❌ Failed to fetch URL for {min_date} (Status: {response.status_code}). Skipping.")
            # Fill empty values for articles if request failed
            for i in range(1, MAX_ARTICLES_PER_DAY + 1):
                 news_data_dict[f'article_{i}_url'] = ""
                 news_data_dict[f'article_{i}_title'] = ""
                 news_data_dict[f'article_{i}_summary'] = ""
                 news_data_dict[f'article_{i}_publish_date'] = ""
                 news_data_dict[f'article_{i}_sentiment_polarity'] = ""
                 news_data_dict[f'article_{i}_sentiment_subjectivity'] = ""
                 news_data_dict[f'article_{i}_sentiment_label'] = ""
            return news_data_dict

        soup = BeautifulSoup(response.text, 'html.parser')

        count = 1
        # Find links within the news results section (Google News specific selectors might need updating)
        # Look for <a> tags within specific containers usually holding news results
        # Common classes/IDs might be 'dbsr', 'WwrzSb', or within <div class="dbsr">...</div> or similar
        # Using a more general approach first, might need refinement based on actual HTML structure
        # Google often uses complex, dynamically loaded structures, so <a> tags directly under certain containers are targeted.
        # The selector below is a common pattern, but might break if Google changes their HTML.
        news_links = soup.find_all('a', href=True) # Start with all links

        print(f"  Found {len(news_links)} <a> tags in the response.")

        for link in news_links:
            link_str = link.get('href')
            # Filter for actual news article links (avoid Google internal links, YouTube, Blogger, etc.)
            # Simplified check for Google News redirect
            if link_str.startswith("http") and "url?q=" in link_str and not any(domain in link_str for domain in ["google.com", "youtube.com", "blogger.com"]):
                # Extract the actual article URL from the Google News redirect URL
                actual_url = link_str.split('url?q=')[1].split('&sa=')[0]
                # Decode URL encoding if necessary (though requests handles most)
                # actual_url = urllib.parse.unquote(actual_url) # Import urllib.parse if needed

                try:
                    print(f"  📰 Fetching article {count}: {actual_url[:50]}...") # Log fetching
                    article = Article(actual_url)
                    article.download()
                    article.parse()

                    # Extract text and title
                    article_text = clean_text(article.text)
                    article_title = clean_text(article.title)
                    publish_date = article.publish_date

                    # Analyze sentiment
                    polarity, subjectivity, sentiment_label = analyze_sentiment(article_text)

                    # Store data
                    news_data_dict[f'article_{count}_url'] = actual_url
                    news_data_dict[f'article_{count}_title'] = article_title
                    news_data_dict[f'article_{count}_summary'] = article_text[:200] + "..." if len(article_text) > 200 else article_text # Store a summary
                    news_data_dict[f'article_{count}_publish_date'] = publish_date.isoformat() if publish_date else ""
                    news_data_dict[f'article_{count}_sentiment_polarity'] = polarity
                    news_data_dict[f'article_{count}_sentiment_subjectivity'] = subjectivity
                    news_data_dict[f'article_{count}_sentiment_label'] = sentiment_label

                    count += 1
                    if count > MAX_ARTICLES_PER_DAY:
                        break # Stop after fetching the desired number

                    # Be respectful to the websites - Increased delay
                    time.sleep(np.random.uniform(3, 5)) # Increased delay

                except Exception as e_article:
                    print(f"  ⚠️  Error processing article {actual_url}: {e_article}")
                    # Fill empty values for this failed article
                    news_data_dict[f'article_{count}_url'] = ""
                    news_data_dict[f'article_{count}_title'] = ""
                    news_data_dict[f'article_{count}_summary'] = ""
                    news_data_dict[f'article_{count}_publish_date'] = ""
                    news_data_dict[f'article_{count}_sentiment_polarity'] = ""
                    news_data_dict[f'article_{count}_sentiment_subjectivity'] = ""
                    news_data_dict[f'article_{count}_sentiment_label'] = ""
                    count += 1
                    if count > MAX_ARTICLES_PER_DAY:
                        break # Stop after attempting the desired number

    except Exception as e:
        print(f"  💥 Error during scraping for {min_date}: {e}")
        # Fill empty values if the whole request fails
        for i in range(1, MAX_ARTICLES_PER_DAY + 1):
             news_data_dict[f'article_{i}_url'] = ""
             news_data_dict[f'article_{i}_title'] = ""
             news_data_dict[f'article_{i}_summary'] = ""
             news_data_dict[f'article_{i}_publish_date'] = ""
             news_data_dict[f'article_{i}_sentiment_polarity'] = ""
             news_data_dict[f'article_{i}_sentiment_subjectivity'] = ""
             news_data_dict[f'article_{i}_sentiment_label'] = ""

    print(f"  ✅ Finished scraping for {min_date} (Found {count-1} articles).")
    return news_data_dict


def google_news_scrapper(start_date_str, end_date_str, output_file_name, search_query=SEARCH_QUERY):
    """Main function to iterate through dates and call the scraper."""
    step_obj = datetime.timedelta(days=1)
    start_date_obj = datetime.datetime.strptime(start_date_str, DATE_FORMAT)
    end_date_obj = datetime.datetime.strptime(end_date_str, DATE_FORMAT)

    all_news_data = []

    current_date_obj = start_date_obj
    while current_date_obj <= end_date_obj:
        current_date_str = current_date_obj.strftime(DATE_FORMAT)
        print(f"\n--- Scraping Date: {current_date_str} ---")
        news_row = run_google_news_scrapper(search_query, current_date_str, current_date_str, output_file_name)
        all_news_data.append(news_row)

        # Move to the next day
        current_date_obj += step_obj

        # Optional: Add a delay between days to be respectful and avoid 429s
        # time.sleep(10) # Increased delay between days

    # Create DataFrame and save
    if all_news_data: # <-- Corrected line
        df = pd.DataFrame(all_news_data, columns=NEWS_COLS)
        # Handle potential missing columns if an article failed to parse
        for col in NEWS_COLS:
            if col not in df.columns:
                df[col] = ""
        df.to_csv(output_file_name, index=False)
        print(f"\n✅ Scraping completed! Results saved to {output_file_name}")
        print(f"  - Scraped from {start_date_str} to {end_date_str}")
        print(f"  - Search Query: '{search_query}'")
        print(f"  - Total rows (dates): {len(df)}")
    else:
        print("\n❌ No data was scraped.")


# --- Main Execution Block ---
if __name__ == "__main__":
    # --- TEST 1: Simple Query for Recent Date ---
    print("--- TEST 1: Simple Query for Recent Date ---")
    test_start_date = '10/10/2025' # A recent date
    test_end_date = '10/10/2025'
    test_output_filename = 'test_recent_simple.csv'
    test_search_query = "Ghana real estate" # Very simple query

    google_news_scrapper(test_start_date, test_end_date, test_output_filename, test_search_query)

    if os.path.exists(test_output_filename):
        print(f"\n--- Test 1 Output Preview ({test_output_filename}) ---")
        try:
            df_test1 = pd.read_csv(test_output_filename)
            print(df_test1.head(5))
        except Exception as e:
            print(f"Could not load test 1 preview: {e}")
    print("\n--- END TEST 1 ---\n")


    # --- TEST 2: Complex Query for Recent Date ---
    print("--- TEST 2: Complex Query for Recent Date ---")
    test2_start_date = '10/11/2025' # Another recent date
    test2_end_date = '10/11/2025'
    test2_output_filename = 'test_recent_complex.csv'
    test2_search_query = SEARCH_QUERY # Use the complex query

    google_news_scrapper(test2_start_date, test2_end_date, test2_output_filename, test2_search_query)

    if os.path.exists(test2_output_filename):
        print(f"\n--- Test 2 Output Preview ({test2_output_filename}) ---")
        try:
            df_test2 = pd.read_csv(test2_output_filename)
            print(df_test2.head(5))
        except Exception as e:
            print(f"Could not load test 2 preview: {e}")
    print("\n--- END TEST 2 ---\n")


    # --- STEP 1: Configuration (for full historical run) ---
    # Define the date range for scraping (adjust as needed)
    # TODO: Consider making these command-line arguments or reading from a config file.
    # --- FETCH HISTORICAL DATA (Last 3 Years) ---
    # end_date_dt = datetime.datetime.now()
    # start_date_dt = end_date_dt - datetime.timedelta(days=3*365) # Roughly 3 years
    # start_date = start_date_dt.strftime(DATE_FORMAT)
    # end_date = end_date_dt.strftime(DATE_FORMAT)

    # Define the output filename for the scraped data
    # output_filename = 'ghana_real_estate_news_sentiment.csv'
    # Use the expanded SEARCH_QUERY defined at the top of the file
    # search_terms = SEARCH_QUERY

    # --- STEP 2: Run the Scraper (Full Historical - COMMENTED OUT FOR TESTING)---
    # print("--- Starting Google News Scraper (Last 3 Years) ---")
    # google_news_scrapper(start_date, end_date, output_filename, search_terms)
    # print("--- Google News Scraper Finished ---")

    # --- STEP 3: (Future) Upload to GCS ---
    # TODO: Implement GCS upload logic here.
    # Example:
    # from google.cloud import storage
    # def upload_to_gcs(local_file_path, bucket_name, destination_blob_name):
    #     client = storage.Client()
    #     bucket = client.bucket(bucket_name)
    #     blob = bucket.blob(destination_blob_name)
    #     blob.upload_from_filename(local_file_path)
    #     print(f"Uploaded {local_file_path} to {destination_blob_name} in bucket {bucket_name}.")
    #
    # upload_to_gcs(output_filename, "asta-insights-data-certain-voyager", f"raw/news_scraping/{output_filename}")

    # --- STEP 4: (Optional) Quick Preview (Full Historical - COMMENTED OUT FOR TESTING) ---
    # Load and display a sample of the results if the file was created
    # if os.path.exists(output_filename):
    #     print(f"\n--- Sample Output Preview ({output_filename}) ---")
    #     try:
    #         df_sample = pd.read_csv(output_filename)
    #         print(df_sample[['date', 'article_1_title', 'article_1_sentiment_label', 'article_1_sentiment_polarity']].head(5))
    #     except Exception as e:
    #         print(f"Could not load sample preview: {e}")

