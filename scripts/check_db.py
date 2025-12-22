import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def print_record(record):
    print(f"\n🏠 PROPERTY: {record.get('title')} ({record.get('location')})")
    print(f"💰 Price: {record.get('price')}")
    
    # 1. Check Gemini Insights
    insights = record.get('insight_cache', {})
    if insights:
        print(f"🤖 AI ROI Verdict: {insights.get('investment_vibe', 'N/A')}")
        print(f"   - Est. Monthly Rent: {insights.get('estimated_monthly_rent', 'N/A')}")
    else:
        print("⚠️ No AI Insights found.")

    # 2. Check Location Intelligence
    loc_intel = record.get('location_intel', {})
    if loc_intel:
        print(f"🌍 Location Context: {loc_intel.get('verdict', 'Neutral')}")
        print(f"   - Tags: {', '.join(loc_intel.get('tags', []))}")
        if loc_intel.get('risks'):
            print(f"   - ⚠️ RISKS: {', '.join(loc_intel.get('risks', []))}")
    else:
        print("⚠️ No Location Intelligence found.")
    print("-" * 50)

def main():
    print("🔍 Querying Supabase for enriched data...\n")

    # Fetch a specific example we saw in the logs
    try:
        target = "Legon Student Housing"
        response = supabase.table("market_listings").select("*").ilike("title", f"%{target}%").limit(1).execute()
        
        if response.data:
            print(f"--- SPECIFIC CHECK: {target} ---")
            print_record(response.data[0])
        else:
            print(f"❌ Could not find '{target}' in DB.")

        # Fetch a few random recent ones
        print("\n--- RECENT ENTRIES SNAPSHOT ---")
        recent = supabase.table("market_listings").select("*").order("insight_last_updated", desc=True).limit(3).execute()
        for row in recent.data:
            if row['title'] != target: # Avoid duplicate print
                print_record(row)

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    main()
