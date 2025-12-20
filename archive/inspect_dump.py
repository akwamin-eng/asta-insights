from google.cloud import storage
import os
import json
from dotenv import load_dotenv

load_dotenv()
bucket_name = os.getenv("GCS_BUCKET_NAME")

def analyze_dump():
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix="raw/property_listings/")
    
    stats = {}
    print(f"{'SITE':<25} | {'TYPE':<10} | {'ITEMS':<10} | {'DATE'}")
    print("-" * 60)
    
    for blob in blobs:
        if not blob.name.endswith(".json"): continue
        parts = blob.name.split('/')
        site = parts[2]
        l_type = parts[3]
        
        try:
            data = json.loads(blob.download_as_string())
            count = len(data)
            date = blob.time_created.strftime("%Y-%m-%d")
            print(f"{site:<25} | {l_type:<10} | {count:<10} | {date}")
        except: continue

if __name__ == "__main__":
    analyze_dump()
