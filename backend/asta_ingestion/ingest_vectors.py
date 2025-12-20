import json
import os
import re
import time
import sys
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai

# --- CONFIG ---
current_script_path = Path(__file__).resolve()
project_root = current_script_path.parents[2]
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

# --- CLIENTS ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_KEY)

INPUT_FILE = "gpc_master_dump_2025_v2.jsonl"
BATCH_SIZE = 10 

def clean_price(price_str):
    if not price_str: return None, "UNKNOWN"
    currency = "USD" if "$" in price_str or "USD" in price_str else "GHS"
    clean_str = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(clean_str), currency
    except:
        return None, "UNKNOWN"

def get_single_embedding(text):
    """
    Generates embedding for a SINGLE string.
    Guarantees a 1-D list of floats output.
    """
    try:
        # Generate for just one item
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        
        # Handle response variations
        if 'embedding' in result:
            return result['embedding']
        elif 'embeddings' in result:
            # If API returns a list, take the first one
            return result['embeddings'][0]
            
        return None
    except Exception as e:
        # print(f"   ⚠️ Gemini Warning: {e}")
        return None

def process_and_upload():
    print(f"🚀 Starting Ingestion (Sequential Mode) from {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    seen_urls = set()
    batch_records = []
    total_indexed = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                raw = json.loads(line)
            except:
                continue

            # URL & Deduplication
            url = raw.get("url")
            if not url:
                title_hash = hashlib.md5(raw.get("title", "unknown").encode()).hexdigest()
                url = f"https://placeholder-gpc.com/{title_hash}"
            
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Prepare Record
            price_val, curr = clean_price(raw.get("price"))
            context_text = f"Title: {raw.get('title')}\nLocation: {raw.get('location')}\nDetails: {raw.get('raw_text_snippet')}"
            
            # --- GENERATE VECTOR IMMEDIATELY (One by One) ---
            # This prevents batch shape mismatch errors
            vector = get_single_embedding(context_text)
            
            # Only proceed if we got a valid vector
            if vector:
                record = {
                    "url": url,
                    "title": raw.get("title"),
                    "price_amount": price_val,
                    "currency": curr,
                    "location_clean": raw.get("location"),
                    "bedrooms": int(raw["bedrooms"]) if raw.get("bedrooms") else None,
                    "bathrooms": int(raw["bathrooms"]) if raw.get("bathrooms") else None,
                    "content_text": context_text,
                    "embedding": vector, # Guaranteed flat list
                    "scraped_at": raw.get("scraped_at")
                }
                batch_records.append(record)
                
                # Sleep briefly to avoid hitting Gemini rate limit (60 req/min free tier)
                time.sleep(0.5) 

            # --- UPLOAD BATCH ---
            if len(batch_records) >= BATCH_SIZE:
                try:
                    supabase.table("gpc_properties").upsert(batch_records, on_conflict="url").execute()
                    total_indexed += len(batch_records)
                    print(f"✅ Indexed {total_indexed} items...")
                except Exception as e:
                    print(f"❌ Upload Error: {e}")
                
                batch_records = []

    # Final Batch
    if batch_records:
        try:
            supabase.table("gpc_properties").upsert(batch_records, on_conflict="url").execute()
            print(f"✅ Final batch of {len(batch_records)} uploaded.")
        except Exception as e:
            print(f"❌ Final Batch Error: {e}")
    
    print(f"🎉 DONE! Successfully indexed {total_indexed + len(batch_records)} items.")

if __name__ == "__main__":
    process_and_upload()
