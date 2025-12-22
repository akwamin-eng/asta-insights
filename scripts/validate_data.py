import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

def print_section(title, data):
    print(f"\n�� {title.upper()}")
    if isinstance(data, dict):
        print(json.dumps(data, indent=2))
    else:
        print(str(data))

def main():
    target_title = "Woodis B. Apartment"
    print(f"🔎 Searching for '{target_title}'...")

    try:
        # Fetch the record
        res = supabase.table("market_listings").select("*").ilike("title", f"%{target_title}%").limit(1).execute()
        
        if not res.data:
            print("❌ Record not found! (Try a generic check if specific name fails)")
            return

        record = res.data[0]
        
        print("\n" + "="*50)
        print(f"🏠 {record['title']}")
        print(f"📍 Location: {record['location']}")
        print(f"�� Price:   GHS {record['price']:,.2f}")
        print("="*50)

        # 1. CHECK GEMINI INSIGHTS (The Deal)
        insights = record.get('insight_cache')
        if insights:
            print_section("🤖 GEMINI INVESTMENT ANALYSIS", {
                "Vibe": insights.get('investment_vibe'),
                "Rent Estimate": insights.get('estimated_monthly_rent'),
                "Strategy": insights.get('recommended_strategy')
            })
        else:
            print("\n❌ MISSING: Gemini Insights")

        # 2. CHECK LOCATION INTEL (The Neighborhood)
        loc_intel = record.get('location_intel')
        if loc_intel:
            print_section("🌍 ASTA LOCATION INTEL", {
                "Verdict": loc_intel.get('verdict'),
                "Tags": loc_intel.get('tags'),
                "Risks": loc_intel.get('risks')
            })
        else:
            print("\n❌ MISSING: Location Intelligence")

        print("\n" + "="*50)
        print("✅ VALIDATION VERDICT:")
        if insights and loc_intel:
            print("   🟢 PERFECT RECORD. Both AI & Location modules fired.")
        else:
            print("   ⚠️ PARTIAL DATA. Check modules.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
