import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from web_scrapers.economic_scraper import get_ghana_economic_data

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

def update_daily_stats():
    print("🌍 Refreshing Ghana Economic Indicators...")
    try:
        data = get_ghana_economic_data()
    except Exception as e:
        print(f"❌ Scraper Error: {e}")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    # Map indicators to the database structure
    indicators = [
        {"indicator_type": "USD_GHS", "value": data.get('usd_ghs'), "recorded_at": today},
        {"indicator_type": "INFLATION", "value": data.get('inflation'), "recorded_at": today}
    ]

    # IDEMPOTENT UPSERT: recorded_at + indicator_type are the unique pair
    for record in indicators:
        if record["value"] is None:
            continue
            
        try:
            supabase.table("economic_indicators").upsert(
                record, 
                on_conflict="indicator_type,recorded_at"
            ).execute()
            print(f"✅ Updated {record['indicator_type']}: {record['value']}")
        except Exception as e:
            print(f"❌ Failed to update {record['indicator_type']}: {e}")

if __name__ == "__main__":
    update_daily_stats()
