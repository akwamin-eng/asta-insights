# asta_data_crawler/config/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for ASTA Data Crawler."""

    # --- Project Metadata ---
    PROJECT_NAME = "ASTA Data Crawler"
    VERSION = "0.1.0"

    # --- API Keys (from environment variables) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") # For official YouTube Data API v3
    # GOOGLE_CLOUD_TRANSLATE_API_KEY = os.getenv("GOOGLE_CLOUD_TRANSLATE_API_KEY") # If using direct API key for Translate

    # --- Google Cloud Platform ---
    GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "certain-voyager-403707")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager") # Your GCS bucket

    # --- Data Source URLs ---
    # Define base URLs for scraping targets here or load from a separate file/db
    LISTING_SITES = [
        # Add actual Ghanaian listing site URLs
        # "https://www.ghanapropertycentre.com/",
        # "https://www.propertyfinderghana.com/",
        # ...
    ]

    # --- RSS Feeds ---
    # Define RSS feed URLs for news sources
    # These need to be validated URLs for Ghanaian news/business/property
    RSS_FEEDS = [
        # Example feeds - REPLACE with ACTUAL VALID RSS FEEDS for Ghanaian News
        # Finding the *correct* RSS URLs is key.
        # Look on the websites themselves for RSS links/icons.
        # "https://www.ghanaweb.com/RSS/News.xml", # Check if this is the correct business/economy feed
        # "https://www.myjoyonline.com/rss.xml", # Check for specific section feeds if available
        # Add more RSS feeds for Ghanaian news/business/property
        # Placeholder feeds for testing
        "https://rss.cnn.com/rss/edition.rss", # Global news, for testing
        "https://feeds.bbci.co.uk/news/world/rss.xml", # BBC World, for testing
        # --- ADD YOUR VALIDATED GHANAIAN RSS FEEDS HERE ---
    ]

    # --- Processing Parameters ---
    DEFAULT_BATCH_SIZE = 100
    MAX_RETRIES = 3
    BASE_DELAY_BETWEEN_REQUESTS = 1.0 # seconds

    # --- LLM Parameters ---
    DEFAULT_LLM_MODEL = "llama3-8b-8192" # Groq model alias
    LLM_TEMPERATURE = 0.2
    LLM_MAX_TOKENS = 1000

    # --- Logging ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Instantiate a global config object
config = Config()

