from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager")

def list_recent_files(limit=10):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    
    print(f"🔍 Checking bucket: {BUCKET_NAME} for recent activity...")
    
    # List all blobs and sort by creation time
    blobs = list(client.list_blobs(BUCKET_NAME))
    blobs.sort(key=lambda x: x.time_created, reverse=True)
    
    if not blobs:
        print("❓ No files found in the bucket at all.")
        return

    print(f"\n--- Top {limit} Most Recent Uploads ---")
    for blob in blobs[:limit]:
        print(f"📅 {blob.time_created.strftime('%Y-%m-%d %H:%M:%S')} UTC | 📂 {blob.name}")

if __name__ == "__main__":
    list_recent_files()
