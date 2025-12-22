import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def update_neighborhood_insights():
    print("📊 Starting Market Stats Aggregation...")

    # We use a single, powerful SQL query via Supabase RPC or a raw call 
    # to calculate stats from unique listings.
    # Note: Using .rpc() requires a saved Postgres function 'calculate_market_insights'.
    
    sql_query = """
    INSERT INTO public.market_insights (
        location, 
        avg_price_sale, 
        avg_price_rent, 
        listing_count, 
        roi_score, 
        sentiment_score, 
        last_updated
    )
    SELECT 
        location,
        AVG(CASE WHEN title ILIKE '%sale%' OR title ILIKE '%buy%' THEN price END) as avg_sale,
        AVG(CASE WHEN title ILIKE '%rent%' OR title ILIKE '%lease%' THEN price END) as avg_rent,
        COUNT(*) as total_listings,
        AVG((insight_cache->>'roi_score')::numeric) as avg_roi,
        AVG((insight_cache->>'sentiment_score')::numeric) as avg_sentiment,
        NOW()
    FROM public.market_listings
    WHERE location IS NOT NULL
    GROUP BY location
    ON CONFLICT (location) DO UPDATE SET
        avg_price_sale = EXCLUDED.avg_price_sale,
        avg_price_rent = EXCLUDED.avg_price_rent,
        listing_count = EXCLUDED.listing_count,
        roi_score = EXCLUDED.roi_score,
        sentiment_score = EXCLUDED.sentiment_score,
        last_updated = NOW();
    """

    try:
        # Executing via a Supabase RPC call for database-side performance
        print("🔗 Syncing neighborhood averages and ROI scores...")
        supabase.postgrest.rpc('execute_sql', {'query': sql_query}).execute()
        print("✅ Market Insights table successfully updated.")
    except Exception as e:
        print(f"⚠️ Aggregation Error: {e}")
        print("💡 Ensure you have the 'execute_sql' RPC function enabled in Supabase.")

if __name__ == "__main__":
    update_neighborhood_insights()
