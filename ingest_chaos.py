import json
import glob
import uuid
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL = "https://tjwwymongjrdsgoxfbtn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRqd3d5bW9uZ2pyZHNnb3hmYnRuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTE5Mjg4OSwiZXhwIjoyMDY2NzY4ODg5fQ.UjTtbZj3wUJ10gdttQUhd6UGMxOtQ_oKo2g9drU3ngI"
# ---------------------

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_location(address_str):
    if not address_str: return "Ghana"
    parts = [p.strip() for p in address_str.split(',')]
    if "Random Street" in address_str: return parts[-1]
    return address_str

def ingest_files():
    files = glob.glob("insights_*.json")
    print(f"Found {len(files)} files to ingest.")
    total_inserted = 0

    for filename in files:
        print(f"Processing {filename}...")
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                items = [data] if isinstance(data, dict) else data

                batch_rows = []
                for item in items:
                    clean_loc = clean_location(item.get('address', ''))
                    lon = float(item.get('longitude', 0))
                    lat = float(item.get('latitude', 0))
                    
                    # 🟢 FIX: GENERATE UNIQUE URL
                    # We use the item's ID or a random UUID to ensure uniqueness
                    unique_id = item.get('id', str(uuid.uuid4()))
                    unique_url = f"import_{unique_id}"

                    row = {
                        "title": f"Market Data in {clean_loc}", 
                        "price": item.get('price'),
                        "location": clean_loc,
                        "source": "data_import_v1",
                        "url": unique_url, # Now Unique!
                        "raw_data": item, 
                        "geo_point": f"POINT({lon} {lat})"
                    }
                    batch_rows.append(row)

                # Insert in chunks of 100 to be safe
                chunk_size = 100
                for i in range(0, len(batch_rows), chunk_size):
                    chunk = batch_rows[i:i + chunk_size]
                    response = supabase.table("market_listings").insert(chunk).execute()
                    count = len(response.data)
                    total_inserted += count
                    print(f"  -> Inserted {count} rows.")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\n✅ MISSION COMPLETE: Successfully injected {total_inserted} intelligence points.")

if __name__ == "__main__":
    ingest_files()
