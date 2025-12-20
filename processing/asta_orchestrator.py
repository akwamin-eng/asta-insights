# asta_run.py
import asyncio
import os
from web_scrapers.economic_scraper import scrape_bog_indicators # REST VERSION
from web_scrapers.insight_scraper import get_market_news_insight # BROWSERBASE VERSION
from processing.llm_tasks.enricher import generate_property_enrichment
from storage.vector_storage import update_vector_data
from supabase import create_client

async def main():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    # 1. FAST & FREE: Get FX Rate
    econ = await scrape_bog_indicators()
    
    # 2. STEALTH: Get Neighborhood News (Optional/Periodic)
    news_context = await get_market_news_insight("East Legon real estate news")
    econ['news_headline'] = news_context

    # 3. Process Properties
    res = supabase.table("asta_properties").select("*").is_("embedding", "NULL").limit(1).execute()
    
    if res.data:
        prop = res.data[0]
        # Calculate normalized prices
        p_usd = float(prop['price']) 
        p_ghs = p_usd * econ['fx_rate']

        # AI Enrichment
        insight, embedding = await generate_property_enrichment(
            prop['title'], prop['address'], p_ghs, econ
        )
        
        # Atomic Save
        update_vector_data(supabase, prop['id'], {
            'ghs': p_ghs, 'usd': p_usd, 'insight': insight, 
            'embedding': embedding, 'econ': econ
        })
        print(f"✅ Enriched {prop['title']} with market news context.")

if __name__ == "__main__":
    asyncio.run(main())