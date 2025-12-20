import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai

# 1. Load Credentials
env_path = Path(".env").resolve()
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Must be SERVICE_ROLE
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

print(f"🔌 Connecting to Supabase: {SUPABASE_URL}")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GEMINI_KEY)
except Exception as e:
    print(f"❌ Client Init Error: {e}")
    exit(1)

INPUT_FILE = "gpc_master_dump_2025.jsonl"

def run_diagnostic():
    print("🚀 Starting Diagnostic Ingest (First 5 Items Only)...")
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        # Read just the first 5 lines
        lines = [f.readline() for _ in range(5)]

    items_to_insert = []
    
    for i, line in enumerate(lines):
        if not line: continue
        raw = json.loads(line)
        
        # 1. Create Context
        context_text = f"Title: {raw.get('title')}\nLocation: {raw.get('location')}\nDetails: {raw.get('raw_text_snippet')}"
        
        # 2. Generate Vector (Gemini)
        print(f"   🤖 Generating vector for item {i+1}...")
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=context_text,
                task_type="retrieval_document"
            )
            vector = result['embedding']
            
            # CHECK VECTOR DIMENSION
            if i == 0:
                print(f"   📏 Vector Dimension: {len(vector)} (Should be 768)")

        except Exception as e:
            print(f"   ❌ Gemini Error: {e}")
            continue

        # 3. Clean Price
        price_str = raw.get("price")
        price_val = None
        if price_str:
             clean_str = "".join([c for c in price_str if c.isdigit() or c == '.'])
             try: price_val = float(clean_str)
             except: pass
        
        # 4. Prepare Record
        record = {
            "url": raw.get("url"),
            "title": raw.get("title"),
            "price_amount": price_val,
            "currency": "GHS", # Simplified for test
            "location_clean": raw.get("location"),
            "content_text": context_text,
            "embedding": vector,
            "scraped_at": raw.get("scraped_at")
        }
        items_to_insert.append(record)

    # 5. ATTEMPT INSERT
    print(f"\n💾 Attempting to insert {len(items_to_insert)} items to Supabase...")
    try:
        response = supabase.table("gpc_properties").upsert(items_to_insert, on_conflict="url").execute()
        print("\n✅ SUCCESS! Response Data:")
        # Print just the first ID to confirm
        print(f"Inserted IDs: {[item.get('id') for item in response.data]}")
        
    except Exception as e:
        print("\n🔥 INSERT FAILED. RAW ERROR MESSAGE:")
        print("------------------------------------------------")
        print(e)
        print("------------------------------------------------")
        print("💡 HINT: If error is 'different vector dimensions', you need to re-run the SQL table creation with vector(768).")

if __name__ == "__main__":
    run_diagnostic()
