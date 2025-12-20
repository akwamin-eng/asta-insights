import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def clean_location(raw_text):
    """
    Extracts the neighborhood from a long string.
    Example: '3 bedroom house in East Legon' -> 'East Legon'
    """
    if not raw_text:
        return "Unknown"
    
    # Common separators in listing titles
    separators = [" in ", " at ", " around ", " near "]
    for sep in separators:
        if sep in raw_text.lower():
            # Take everything after the separator
            parts = raw_text.lower().split(sep)
            return parts[-1].strip().title()
            
    return raw_text.strip().title()

def aggregate_stats():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    print("📊 Fetching raw listings for aggregation...")
    # Get all listings
    response = supabase.from_('market_listings').select('location, price').execute()
    listings = response.data

    if not listings:
        print("❌ No listings found to aggregate.")
        return

    # Grouping logic
    stats = {}
    for item in listings:
        raw_loc = item.get('location')
        loc = clean_location(raw_loc)
        price = item.get('price', 0) or 0

        if loc not in stats:
            stats[loc] = {'prices': [], 'count': 0}
        
        if price > 0:
            stats[loc]['prices'].append(price)
        stats[loc]['count'] += 1

    print(f"🧹 Cleaned {len(listings)} listings into {len(stats)} neighborhoods.")

    # Upsert into market_insights
    for loc, data in stats.items():
        avg_price = sum(data['prices']) / len(data['prices']) if data['prices'] else 0
        
        # This will update if exists, or insert if new
        supabase.from_('market_insights').upsert({
            'location': loc,
            'avg_price_sale': avg_price,
            'listing_count': data['count'],
            'last_updated': 'now()'
        }, on_conflict='location').execute()

    print("✅ Market insights cleaned and updated successfully.")

if __name__ == "__main__":
    aggregate_stats()
