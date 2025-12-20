import os
import google.generativeai as genai
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# --- CONFIG ---
env_path = Path(".env").resolve()
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_KEY)

def debug_query():
    query = input("\n🔎 Enter search term (e.g., 'house in accra'): ")
    
    print("   1. Generating Vector...")
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )
        vector = result['embedding']
    except Exception as e:
        print(f"   ❌ Gemini Error: {e}")
        return

    print("   2. Sending to Database (Threshold: 0.0)...")
    try:
        # We ask for a threshold of 0.0 to see EVERYTHING
        response = supabase.rpc(
            "match_properties",
            {
                "query_embedding": vector,
                "match_threshold": 0.0, 
                "match_count": 5
            }
        ).execute()
        
        matches = response.data
        
        print(f"\n   ✅ Database returned {len(matches)} raw matches.")
        print("   " + "-"*50)
        
        for i, item in enumerate(matches):
            score = item.get('similarity', 0)
            print(f"   Match #{i+1}")
            print(f"   Score: {score:.4f}  <-- THIS IS THE IMPORTANT NUMBER")
            print(f"   Title: {item['title']}")
            print(f"   Loc:   {item['location_clean']}")
            print("   " + "-"*50)
            
    except Exception as e:
        print(f"   ❌ Database Error: {e}")

if __name__ == "__main__":
    while True:
        debug_query()
