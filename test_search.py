import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from fastembed import TextEmbedding

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def test_query(user_query):
    print(f"\n🔎 Searching for: '{user_query}'")
    
    # 1. Convert text to vector
    # list(model.embed(...)) returns a list of vectors. We take the first one.
    query_vector = list(model.embed([user_query]))[0].tolist()
    
    # 2. Call the Supabase RPC function
    params = {
        "query_embedding": query_vector,
        "match_threshold": 0.60, # 60% similarity or higher
        "match_count": 5
    }
    
    try:
        response = supabase.rpc("search_market_listings", params).execute()
        
        # 3. Print Results
        if not response.data:
            print("   ❌ No matches found.")
        else:
            for i, item in enumerate(response.data):
                print(f"   {i+1}. [{item['similarity']:.2f}] {item['title']}")
                print(f"       📍 {item['location']} | 💰 {item['price']}")
                print(f"       🔗 {item['url']}")
                print("-" * 40)
                
    except Exception as e:
        print(f"   ⚠️ Database Error: {e}")

if __name__ == "__main__":
    # Try different complex queries to test AI understanding
    test_query("3 bedroom house in East Legon with a pool")
    test_query("affordable apartment for rent in Osu under 2000")
