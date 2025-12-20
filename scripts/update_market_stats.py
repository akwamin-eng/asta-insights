import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Dictionary to normalize common Ghana neighborhood variations
NEIGHBORHOOD_MAP = {
    "Dzworwulu": "Dzorwulu",
    "Dzorwulo": "Dzorwulu",
    "East Lagon": "East Legon",
    "E. Legon": "East Legon",
    "Legon East": "East Legon",
    "Shiashie": "East Legon", # Often grouped together
    "Airport Hills": "Airport Residential",
    "Airport Resi": "Airport Residential",
    "Spintex Road": "Spintex",
    "Adjiringano": "Adjiringanor",
    "Adjirigano": "Adjiringanor",
    "West Lagon": "West Legon",
    "Osu Re": "Osu",
    "Teshie Nungua": "Teshie",
    "Nungua Barrier": "Nungua"
}

def clean_location(raw_text):
    if not raw_text:
        return "Unknown"
    
    # 1. Extract location after separators
    clean_name = raw_text.strip()
    separators = [" in ", " at ", " around ", " near "]
    for sep in separators:
        if sep in raw_text.lower():
            clean_name = raw_text.lower().split(sep)[-1].strip().title()
            break
            
    # 2. Normalize based on the Mapping Dictionary
    # We check if the extracted name matches any of our "tricky" keys
    for variation, official_name in NEIGHBORHOOD_MAP.items():
        if variation.lower() in clean_name.lower():
            return official_name
            
    return clean_name.title()

def aggregate_stats():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    print("📊 Fetching listings for mapped aggregation...")
    response = supabase.from_('market_listings').select('location, price').execute()
    listings = response.data

    if not listings:
        print("❌ No listings found.")
        return

    stats = {}
    for item in listings:
        loc = clean_location(item.get('location'))
        price = item.get('price', 0) or 0

        if loc not in stats:
            stats[loc] = {'prices': [], 'count': 0}
        
        if price > 0:
            stats[loc]['prices'].append(price)
        stats[loc]['count'] += 1

    print(f"🧹 Normalizing {len(listings)} listings into {len(stats)} official zones.")

    for loc, data in stats.items():
        avg_price = sum(data['prices']) / len(data['prices']) if data['prices'] else 0
        supabase.from_('market_insights').upsert({
            'location': loc,
            'avg_price_sale': avg_price,
            'listing_count': data['count'],
            'last_updated': 'now()'
        }, on_conflict='location').execute()

    print("✅ Mapped market insights updated.")

if __name__ == "__main__":
    aggregate_stats()
