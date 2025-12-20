# asta_data_crawler/storage/supabase_connector.py
import os
import logging
from typing import List, Dict, Any
from supabase import create_client, Client
# Import the central config
from config.config import config

# Configure logger for this module
logger = logging.getLogger(__name__)

class SupabaseConnector:
    """Handles connection and data insertion to Supabase."""

    def __init__(self):
        """Initialize the Supabase client."""
        self.client: Client = None
        self._connect()

    def _connect(self):
        """Create the Supabase client using credentials from config."""
        url = config.SUPABASE_URL
        key = config.SUPABASE_KEY
        
        if not url or not key:
            raise ValueError("❌ Missing SUPABASE_URL or SUPABASE_KEY in config. Please check your .env file.")

        try:
            self.client = create_client(url, key)
            logger.info("✅ Connected to Supabase successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise

    def insert_rss_articles(self, articles: List[Dict[str, Any]], table_name: str = "ghana_market_insights") -> int:
        """
        Inserts a list of RSS article dictionaries into a Supabase table.
        Returns the number of successfully inserted articles.
        """
        if not self.client:
            logger.error("⚠️  Supabase client not initialized.")
            return 0

        if not articles:
            logger.info("ℹ️  No articles provided for insertion.")
            return 0

        logger.info(f"📤 Inserting {len(articles)} RSS articles into table '{table_name}'...")
        inserted_count = 0

        # Prepare data for batch upsert
        # Map article fields to Supabase table columns
        # Adjust field names if your Supabase table schema differs
        supabase_articles = []
        for article in articles:
            supabase_article = {
                "video_id": article.get("id"), # Using 'id' as 'video_id' for now, adjust if needed
                "title": article.get("title"),
                "hotspots": [], # Initialize as empty list, will be populated by NLP
                "cost_drivers": [], # Initialize as empty list, will be populated by NLP
                "infrastructure": [], # Initialize as empty list, will be populated by NLP
                "market_signals": [], # Initialize as empty list, will be populated by NLP
                "confidence": "low", # Default confidence, will be updated by NLP
                "publish_time": article.get("published_iso"),
                "insight_source": "rss_feed", # Indicate source
                # Add other fields if your table schema requires them
                # e.g., "url": article.get("link"),
                # e.g., "summary": article.get("summary"),
                # e.g., "feed_url": article.get("feed_url"),
                # e.g., "fetched_at": article.get("fetched_at"),
            }
            supabase_articles.append(supabase_article)

        try:
            # Use upsert to handle potential duplicates based on 'video_id' (or 'id' if it's the primary key)
            # Ensure 'video_id' (or the primary key column) has a unique constraint/index in Supabase
            response = self.client.table(table_name).upsert(supabase_articles).execute()
            inserted_count = len(response.data) if response.data else 0
            logger.info(f"✅ Successfully inserted/updated {inserted_count}/{len(articles)} RSS articles into '{table_name}'.")
            
        except Exception as e:
            logger.error(f"❌ Error inserting RSS articles into '{table_name}': {e}")
            # Log the first article for debugging structure
            if supabase_articles:
                logger.debug(f"  Sample article structure: {supabase_articles[0]}")

        return inserted_count

# Example usage if run directly
if __name__ == "__main__":
    # This is just a placeholder/example. Actual usage would be in main pipeline.
    import sys
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO), stream=sys.stdout)
    
    connector = SupabaseConnector()
    # Example dummy data (would come from rss_reader in real use)
    dummy_articles = [
        {
            "id": "test_article_1",
            "title": "Test Article 1",
            "summary": "This is a summary of test article 1.",
            "link": "https://example.com/test1",
            "published_iso": "2023-10-27T10:00:00Z",
            "feed_url": "https://example.com/rss.xml",
            "fetched_at": "2023-10-27T11:00:00Z"
        }
    ]
    count = connector.insert_rss_articles(dummy_articles)
    print(f"Inserted {count} dummy articles.")

