import os
import asyncio
import random
import functools
from datetime import datetime
from dotenv import load_dotenv
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode, ProxyConfig

load_dotenv()

def get_proxy_config():
    """Builds ProxyConfig from .env credentials."""
    server = os.getenv("PROXY_SERVER")
    user = os.getenv("PROXY_USER")
    password = os.getenv("PROXY_PASS")
    
    if not server:
        return None
    
    return ProxyConfig(server=server, username=user, password=password)

def retry_with_backoff(retries=3, base_delay=5):
    """Decorator for async functions to retry with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        print(f"❌ Final attempt failed: {e}")
                        raise e
                    
                    wait_time = (base_delay * (2 ** attempt)) + random.uniform(0, 5)
                    print(f"⚠️ Attempt {attempt+1} failed. Retrying in {wait_time:.1f}s... (Error: {e})")
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    return decorator

def get_stealth_browser_config():
    """Randomized browser fingerprinting."""
    viewports = [{"width": 1920, "height": 1080}, {"width": 1440, "height": 900}]
    vp = random.choice(viewports)
    
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        enable_stealth=True,
        user_agent_mode="random",
        proxy_config=get_proxy_config(),
        viewport_width=vp["width"],
        viewport_height=vp["height"],
        extra_args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )

def get_human_run_config(extraction_strategy):
    """Human-like interaction patterns."""
    # Calculate the random delay BEFORE creating the config object
    random_delay = random.uniform(2.0, 5.0)
    
    return CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS,
        # Use the correct parameter for your version
        delay_before_return_html=random_delay,
        js_code="""
        (async () => {
            // Random scroll jitter to simulate reading
            for(let i=0; i<3; i++) {
                window.scrollBy(0, Math.random() * 300);
                await new Promise(r => setTimeout(r, 500 + Math.random() * 1000));
            }
        })();
        """
    )
