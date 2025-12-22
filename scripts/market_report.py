import os
import json
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

def normalize_insights(data):
    """
    Helper to safely extract the insight dict, whether it was saved 
    as a dict {...} or a list [{...}].
    """
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            return data[0]
        return {}
    if isinstance(data, dict):
        return data
    return {}

def main():
    print("📊 GENERATING ASTA MARKET REPORT...\n")
    
    try:
        # Fetch all records that have insights
        response = supabase.table("market_listings").select("*").not_.is_("insight_cache", "null").execute()
        listings = response.data
        
        if not listings:
            print("❌ No enriched listings found.")
            return

        total = len(listings)
        strategies = Counter()
        vibes = Counter()
        high_roi_picks = []

        print(f"✅ Analyzed {total} Properties.\n")

        for item in listings:
            raw_insights = item.get('insight_cache')
            
            # --- FIX: Normalize the data before using .get() ---
            insights = normalize_insights(raw_insights)
            
            if not insights: continue
            
            # Count Strategies
            strat = insights.get('recommended_strategy', 'Unknown')
            strategies[strat] += 1
            
            # Count Vibes (Top 3 words to group them loosely)
            vibe = insights.get('investment_vibe', 'Unknown')
            # Normalize vibe slightly for grouping
            vibe_lower = str(vibe).lower()
            if "overpriced" in vibe_lower: vibes["Overpriced"] += 1
            elif "gem" in vibe_lower: vibes["Hidden Gem"] += 1
            elif "cash flow" in vibe_lower: vibes["Cash Flow"] += 1
            elif "avoid" in vibe_lower: vibes["Avoid"] += 1
            else: vibes["Neutral/Other"] += 1

            # Find Top Picks (ROI Score > 7)
            try:
                roi = float(insights.get('roi_score', 0))
                if roi >= 8:
                    high_roi_picks.append({
                        "title": item.get('title'),
                        "price": item.get('price'),
                        "location": item.get('location'),
                        "roi": roi,
                        "vibe": vibe
                    })
            except: pass

        # --- PRINT REPORT ---
        
        print("📈 INVESTMENT STRATEGY BREAKDOWN")
        print("-" * 30)
        for strat, count in strategies.most_common():
            print(f"   • {strat}: {count} listings")
            
        print("\n🧠 AI SENTIMENT (VIBE)")
        print("-" * 30)
        for vibe, count in vibes.most_common():
            print(f"   • {vibe}: {count}")

        print("\n💎 TOP 5 'HIGH ROI' PICKS (Score 8+)")
        print("-" * 30)
        # Sort by ROI descending
        high_roi_picks.sort(key=lambda x: x['roi'], reverse=True)
        
        for pick in high_roi_picks[:5]:
            title = pick['title'] or "Unknown Title"
            print(f"   🌟 {title[:40]}...")
            print(f"      �� {pick['location']} | 💰 GHS {pick['price']:,.0f}")
            print(f"      🤖 {pick['vibe']} (Score: {pick['roi']}/10)")
            print("")

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
