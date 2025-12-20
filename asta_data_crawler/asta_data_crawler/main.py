# asta_data_crawler/main.py
"""
Main entry point for the ASTA Data Crawler.
"""
import asyncio
import logging
import sys
from datetime import datetime
# Import the central config
from config.config import config

# Import new components
from data_sources.news_scrapers.rss_reader import fetch_all_rss_articles
from storage.supabase_connector import SupabaseConnector

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO), stream=sys.stdout)
logger = logging.getLogger(__name__)

async def main():
    """Main asynchronous function."""
    start_time = datetime.now()
    logger.info(f"🚀 Starting {config.PROJECT_NAME} v{config.VERSION}...")
    logger.info("🔧 Configuration loaded successfully.")

    try:
        # --- 1. Fetch RSS Articles ---
        logger.info("--- Step 1: Fetching RSS Articles ---")
        # Fetch articles from RSS feeds (using config.RSS_FEEDS)
        # Adjust max_feeds and max_articles_per_feed as needed for testing/production
        rss_articles = fetch_all_rss_articles(max_feeds=5, max_articles_per_feed=10) # Example: First 5 feeds, 10 articles each

        if not rss_articles:
            logger.warning("⚠️  No RSS articles were fetched. Skipping further processing.")
            logger.info(f"✅ {config.PROJECT_NAME} run completed (no articles). Duration: {datetime.now() - start_time}")
            return "✅ Pipeline completed (no articles)!", 200

        logger.info(f"📦 Fetched {len(rss_articles)} RSS articles.")

        # --- 2. Store RSS Articles in Supabase ---
        logger.info("--- Step 2: Storing RSS Articles in Supabase ---")
        supabase_conn = SupabaseConnector()
        inserted_count = supabase_conn.insert_rss_articles(rss_articles, table_name="ghana_market_insights")
        logger.info(f"💾 Stored {inserted_count} RSS articles in Supabase.")

        # --- 3. (Future) Process Articles with LLM (Groq) ---
        # This is where you would call Groq to analyze the 'summary' or full content
        # and update the 'hotspots', 'cost_drivers', etc. in Supabase.
        # We'll implement this in a later step.

        # --- 4. (Future) Compute Index ---
        # This is where you would call compute_index or similar logic.
        # We'll implement this in a later step.

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"✅ {config.PROJECT_NAME} run completed successfully! Total duration: {duration}.")
        return "✅ Pipeline completed!", 200

    except Exception as e:
        error_time = datetime.now()
        logger.error(f"💥 {config.PROJECT_NAME} failed: {e}")
        # Print the full traceback for detailed debugging
        import traceback
        logger.error(traceback.format_exc())
        return f"❌ Failed: {str(e)}", 500

if __name__ == "__main__":
    # Run the async main function
    result_message, status_code = asyncio.run(main())
    print(result_message) # Print final message to stdout
    sys.exit(0 if status_code == 200 else 1) # Exit with appropriate code

