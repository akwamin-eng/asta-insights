import os
from google import genai
from google.genai import types
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Clients
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

def test_semantic_search(user_query):
    print(f"\n🔎 User searching for: '{user_query}'")
    
    # 2. Convert text to vector
    try:
        # FIX: Removed 'title' parameter because it is not allowed for RETRIEVAL_QUERY
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=user_query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        query_vector = result.embeddings[0].values
    except Exception as e:
        print(f"❌ Embedding Error: {e}")
        return

    # 3. Call the Database Search Function
    # We call the RPC function we created in SQL earlier
    response = supabase.rpc('search_listings', {
        'query_embedding': query_vector,
        'match_threshold': 0.5, # 50% similarity
        'match_count': 3
    }).execute()

    # 4. Show Results
    if response.data:
        print(f"✅ Found {len(response.data)} matches:")
        for item in response.data:
            print(f"   🏠 {item['title']}")
            print(f"      📍 {item['location']} | 💰 {item['price']}")
            print(f"      🔗 Similarity: {round(item['similarity'] * 100, 1)}%")
            print("   ---")
    else:
        print("🤷 No matches found. Try lowering threshold or changing query.")

if __name__ == "__main__":
    # Test 1: Vague concept
    test_semantic_search("modern apartment in a safe area")
    
    # Test 2: Specific location "vibe"
    test_semantic_search("luxury home near airport")
