# storage/supabase_connector.py
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
        supabase_articles = []
        for article in articles:
            supabase_article = {
                "video_id": article.get("id"), # Using 'id' as 'video_id' for now, adjust if needed
                "title": article.get("title"),
                "hotspots": article.get("hotspots", []), # Initialize as empty list if not present
                "cost_drivers": article.get("cost_drivers", []),
                "infrastructure": article.get("infrastructure", []),
                "market_signals": article.get("market_signals", []),
                "confidence": article.get("confidence", "low"),
                "publish_time": article.get("published_iso"),
                "insight_source": article.get("insight_source", "rss_feed"), # Indicate source
                # Add other fields if your table schema requires them
            }
            supabase_articles.append(supabase_article)

        try:
            # Use upsert to handle potential duplicates based on 'video_id' (or primary key)
            response = self.client.table(table_name).upsert(supabase_articles).execute()
            inserted_count = len(response.data) if response.data else 0
            logger.info(f"✅ Successfully inserted/updated {inserted_count}/{len(articles)} RSS articles into '{table_name}'.")
            
        except Exception as e:
            logger.error(f"❌ Error inserting RSS articles into '{table_name}': {e}")
            # Log the first article for debugging structure
            if supabase_articles:
                logger.debug(f"  Sample article structure: {supabase_articles[0]}")

        return inserted_count

    # --- NEW FUNCTION: insert_youtube_insights ---
    def insert_youtube_insights(self, insights: List[Dict[str, Any]], table_name: str = "ghana_market_insights") -> int:
        """
        Inserts a list of YouTube insight dictionaries into a Supabase table.
        Returns the number of successfully inserted insights.
        """
        if not self.client:
            logger.error("⚠️  Supabase client not initialized.")
            return 0

        if not insights:
            logger.info("ℹ️  No YouTube insights provided for insertion.")
            return 0

        logger.info(f"📤 Inserting {len(insights)} YouTube insights into table '{table_name}'...")
        inserted_count = 0

        # Prepare data for batch upsert
        # Map insight fields to Supabase table columns
        supabase_insights = []
        for insight in insights:
            supabase_insight = {
                "video_id": insight.get("video_id"),
                "title": insight.get("title"),
                "hotspots": insight.get("hotspots", []), # List of strings
                "cost_drivers": insight.get("cost_drivers", []), # List of strings
                "infrastructure": insight.get("infrastructure", []), # List of strings
                "market_signals": insight.get("market_signals", []), # List of strings
                "confidence": insight.get("confidence", "low"), # String
                "publish_time": insight.get("publish_time"), # ISO string
                "insight_source": insight.get("insight_source", "youtube_unknown"), # String indicating source (transcript/metadata)
                # Add other fields if your table schema requires them
            }
            supabase_insights.append(supabase_insight)

        try:
            # Use upsert to handle potential duplicates based on 'video_id' (ensure it's a primary key or has unique constraint)
            response = self.client.table(table_name).upsert(supabase_insights).execute()
            inserted_count = len(response.data) if response.data else 0
            logger.info(f"✅ Successfully inserted/updated {inserted_count}/{len(insights)} YouTube insights into '{table_name}'.")
            
        except Exception as e:
            logger.error(f"❌ Error inserting YouTube insights into '{table_name}': {e}")
            # Log the first insight for debugging structure
            if supabase_insights:
                logger.debug(f"  Sample insight structure: {supabase_insights[0]}")

        return inserted_count
    # --- END OF NEW FUNCTION ---

# Example usage if run directly
if __name__ == "__main__":
    # This is just a placeholder/example. Actual usage would be in main pipeline.
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout) # Use INFO for direct run
    
    connector = SupabaseConnector()
    # Example dummy data (would come from rss_reader or youtube analysis in real use)
    dummy_articles = [
        {
            "id": "test_article_1_rss",
            "title": "Test Article 1 (RSS)",
            "hotspots": ["Accra", "investing in Ghana"],
            "cost_drivers": ["cement prices"],
            "infrastructure": ["new road project"],
            "market_signals": ["demand rising"],
            "confidence": "medium",
            "publish_time": "2023-10-27T10:00:00Z",
            "insight_source": "rss_feed"
        },
        {
            "video_id": "test_video_1_yt",
            "title": "Test Video 1 (YouTube)",
            "hotspots": ["Kumasi", "building in Ghana"],
            "cost_drivers": ["rod iron"],
            "infrastructure": ["airport expansion"],
            "market_signals": ["rental yields compressing"],
            "confidence": "high",
            "publish_time": "2023-10-28T11:00:00Z",
            "insight_source": "youtube_transcript"
        }
    ]
    count_rss = connector.insert_rss_articles(dummy_articles[:1]) # Insert first (RSS) item
    count_yt = connector.insert_youtube_insights(dummy_articles[1:]) # Insert second (YouTube) item
    print(f"Inserted {count_rss} dummy RSS article and {count_yt} dummy YouTube insight.")

