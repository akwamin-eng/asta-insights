import json

# --- CONFIGURATION ---
INPUT_FILE = "jiji_dump_raw.json"

def get_dummy_embedding(text):
    # Replace with your actual embedding logic later
    return [0.0] * 384 

def run_processing():
    print(f"📂 Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            jiji_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: Run jiji_harvester.py first.")
        return

    vectors_to_upsert = []

    print("⚙️  Processing and Tagging...")
    for item in jiji_data:
        record_id = f"jiji_{item['external_id']}"
        text_to_embed = f"{item['title']} in {item['location']}. Price: {item['price']} GHS."
        vector = get_dummy_embedding(text_to_embed)
        
        metadata = {
            "source": item['source'], 
            "title": item['title'],
            "price": item['price'],
            "location": item['location'],
            "url": item['url'],
            "currency": "GHS"
        }
        
        vectors_to_upsert.append({
            "id": record_id,
            "values": vector,
            "metadata": metadata
        })

    print(f"✅ Ready to Upsert {len(vectors_to_upsert)} records.")
    if vectors_to_upsert:
        print("\n--- SAMPLE RECORD ---")
        print(json.dumps(vectors_to_upsert[0], indent=2))

if __name__ == "__main__":
    run_processing()
