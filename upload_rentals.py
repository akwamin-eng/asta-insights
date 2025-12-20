import json
import os
import re
import math
from dotenv import load_dotenv
from supabase import create_client, Client
from fastembed import TextEmbedding

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
INPUT_FILE = "meqasa_rentals_dump.json"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("🧠 Loading AI Model...")
model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def clean_price(price_str):
    if not price_str: return 0, "GHS"
    currency = "USD" if "$" in price_str or "USD" in price_str else "GHS"
    clean = re.sub(r'[^\d]', '', price_str)
    return (int(clean), currency) if clean else (0, currency)

def run():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Run meqasa_rentals_harvester.py first!")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"🚀 Uploading {len(data)} rentals...")
    batch = []
    
    for i, item in enumerate(data):
        price_val, currency = clean_price(item['price'])
        
        # Enhanced text for embedding "Apartment for rent in Osu..."
        text_content = f"{item['title']}. For Rent. Price: {price_val} {currency}. {item['location']}"
        embedding = list(model.embed([text_content]))[0].tolist()
        
        record = {
            "id": item['id'],
            "source": "Meqasa",
            "title": item['title'],
            "price": price_val,
            "currency": currency,
            "location": item['location'],
            "url": item['url'],
            "bedrooms": int(item['beds']) if str(item['beds']).isdigit() else 0,
            "content": text_content,
            "embedding": embedding,
            "metadata": {**item, "type": "Rent"}
        }
        batch.append(record)
        
        if len(batch) >= 50:
            supabase.table("market_listings").upsert(batch).execute()
            print(f"   ✅ Batch {math.ceil((i+1)/50)} uploaded.")
            batch = []

    if batch:
        supabase.table("market_listings").upsert(batch).execute()
        print("✅ Final batch uploaded.")

if __name__ == "__main__":
    run()
