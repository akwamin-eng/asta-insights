# asta_data_crawler/main.py
"""
Main entry point for the ASTA Data Crawler.
"""
import asyncio
import logging
from config.config import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

async def main():
    """Main asynchronous function."""
    logger.info(f"🚀 Starting {config.PROJECT_NAME} v{config.VERSION}...")
    logger.info("🔧 Configuration loaded successfully.")

    # TODO: Implement the orchestrator logic here
    # e.g., instantiate scrapers, run them, process data, store data

    logger.info(f"✅ {config.PROJECT_NAME} run completed.")

if __name__ == "__main__":
    asyncio.run(main())
