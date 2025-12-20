import json
import os
import math
from dotenv import load_dotenv
from supabase import create_client, Client
from fastembed import TextEmbedding

# --- CONFIGURATION ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
INPUT_FILE = "meqasa_ready_for_db.json"
BATCH_SIZE = 50 

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastEmbed (Lighter, Faster, No PyTorch needed)
print("🧠 Loading AI Model (all-MiniLM-L6-v2)...")
model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def run_upload():
    print(f"📂 Loading data from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    print(f"🚀 Preparing to upload {len(data)} records to 'market_listings'...")

    batch_buffer = []
    
    for i, item in enumerate(data):
        # 1. Get the text for embedding
        text_content = item.get('_text_to_embed', '')
        if not text_content:
            text_content = f"{item['metadata']['title']} in {item['metadata']['location']}"

        # 2. Generate Vector
        # model.embed returns a generator, convert to list -> first item -> list of floats
        embedding = list(model.embed([text_content]))[0].tolist()
        
        # 3. Map to Table Schema
        record = {
            "id": item['id'],
            "source": item['metadata']['source'],
            "title": item['metadata']['title'],
            "price": item['metadata']['price'],
            "currency": item['metadata']['currency'],
            "location": item['metadata']['location'],
            "url": item['metadata']['url'],
            "bedrooms": item['metadata']['beds'],
            "content": text_content,
            "embedding": embedding,
            "metadata": item['metadata']
        }
        
        batch_buffer.append(record)
        
        # 4. Upload Batch
        if len(batch_buffer) >= BATCH_SIZE:
            try:
                # Upsert to prevent duplicates
                supabase.table("market_listings").upsert(batch_buffer).execute()
                print(f"   ✅ Batch {math.ceil((i+1)/BATCH_SIZE)}: Uploaded {len(batch_buffer)} items.")
            except Exception as e:
                print(f"   ❌ Error on batch: {str(e)[:150]}...")
            
            batch_buffer = [] 

    # Final Batch
    if batch_buffer:
        supabase.table("market_listings").upsert(batch_buffer).execute()
        print(f"   ✅ Final Batch: Uploaded {len(batch_buffer)} items.")

    print("\n🎉 DONE! Meqasa data is live in the Vector Database.")

if __name__ == "__main__":
    run_upload()
