import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def debug_db():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    print("🔍 Inspecting 'market_listings' table...")

    # 1. Count Total Listings
    # Note: 'head=True' asks for just the count
    count_response = supabase.from_('market_listings').select('*', count='exact', head=True).execute()
    total_count = count_response.count
    print(f"📊 Total Listings in DB: {total_count}")

    if total_count == 0:
        print("⚠️ Warning: Table is empty. Run your scraper first!")
        return

    # 2. Check a raw sample to see what 'embedding' looks like
    print("🔬 Fetching one sample row...")
    sample = supabase.from_('market_listings').select('id, title, embedding').limit(1).execute()
    
    if sample.data:
        row = sample.data[0]
        emb = row.get('embedding')
        status = "✅ Has Vector" if emb else "❌ NULL"
        print(f"   Title: {row.get('title')}")
        print(f"   Embedding Field Value: {emb}")
        print(f"   Status: {status}")
    
    # 3. Explicitly count NULLs using a different filter approach if needed
    # We fetch IDs where embedding is null
    null_check = supabase.from_('market_listings').select('id', count='exact', head=True).is_('embedding', 'null').execute()
    print(f"📉 Rows with NULL embedding (Server Count): {null_check.count}")

if __name__ == "__main__":
    debug_db()
