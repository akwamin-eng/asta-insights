import os
import time
import re
import uuid
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Import verified modules
from scripts.enricher import get_asta_insights
from web_scrapers.economic_scraper import get_ghana_economic_data
from processing.location_intelligence import LocationIntelligence

load_dotenv()

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

loc_intel = LocationIntelligence()

# --- GEOGRAPHIC CONSTANTS ---
GHANA_MIN_LAT = 4.5
GHANA_MAX_LAT = 12.0
GHANA_MIN_LON = -4.0
GHANA_MAX_LON = 2.0
FOREIGN_KEYWORDS = ['nigeria', 'togo', 'benin', 'ivory coast', 'usa', 'united states', 'uk', 'london', 'lagos', 'abuja']

def is_valid_ghana_location(row):
    try:
        lat = float(row.get('latitude', 0))
        lon = float(row.get('longitude', 0))
        if lat != 0 or lon != 0:
            if not (GHANA_MIN_LAT <= lat <= GHANA_MAX_LAT): return False, "Bad Lat/Lon"
            if not (GHANA_MIN_LON <= lon <= GHANA_MAX_LON): return False, "Bad Lat/Lon"
    except: pass

    address = str(row.get('address', '')).lower()
    for word in FOREIGN_KEYWORDS:
        if f" {word} " in f" {address} " or address.endswith(word):
            return False, f"Foreign Address: {word}"
    return True, "Valid"

def normalize_text(text):
    if pd.isna(text): return "unknown"
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def normalize_location(text):
    if pd.isna(text): return "unknown"
    clean = str(text).lower()
    for word in ['ghana', 'region', 'greater accra', 'greater', 'area']:
        clean = clean.replace(word, '')
    return re.sub(r'[^a-z0-9]', '', clean)

def clean_nan(data):
    """Recursively replace NaN with None for JSON safety."""
    if isinstance(data, dict):
        return {k: clean_nan(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_nan(v) for v in data]
    elif isinstance(data, float) and np.isnan(data):
        return None
    return data

def main():
    print("📈 Fetching live economic data...")
    try:
        eco_data = get_ghana_economic_data()
    except:
        eco_data = {"usd_ghs": 15.0}
    
    input_file = "data/ghana_properties_raw.csv"
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found.")
        return

    # 1. LOAD & FILTER
    df = pd.read_csv(input_file)
    print(f"📥 Loaded {len(df)} rows.")
    
    valid_rows = []
    for index, row in df.iterrows():
        is_valid, _ = is_valid_ghana_location(row)
        if is_valid: valid_rows.append(row)
    df = pd.DataFrame(valid_rows)
    print(f"🌍 Geo-Filter passed: {len(df)} rows.")

    # 2. DEDUPLICATE
    df['clean_title'] = df['title'].apply(normalize_text)
    df['clean_address'] = df['address'].apply(normalize_location)
    df['fingerprint'] = df['clean_title'] + "|" + df['clean_address']
    
    df_clean = df.drop_duplicates(subset=['fingerprint'], keep='first').copy()
    print(f"✂️  Unique candidates: {len(df_clean)}")

    # 3. DB CHECK (Load existing fingerprints to skip work)
    try:
        db_res = supabase.table("market_listings").select("title, location").execute()
        db_fingerprints = {f"{normalize_text(i.get('title'))}|{normalize_location(i.get('location'))}" for i in db_res.data}
    except: db_fingerprints = set()

    # 4. ENRICHMENT LOOP
    enriched_count = 0
    
    # Process only items we haven't seen in the DB
    to_process = []
    for index, row in df_clean.iterrows():
        fingerprint = row['fingerprint']
        if fingerprint not in db_fingerprints:
            to_process.append(row)

    print(f"🧠 Actually processing {len(to_process)} new items (others are already in DB)...")

    for i, row in enumerate(to_process):
        title = row.get('title', "Unknown")
        location = row.get('address', "Accra")
        price = row.get('price', "0")
        listing_id = str(row.get('id', f"gen_{i}"))

        print(f"🪄 [{i+1}/{len(to_process)}] Enriching: {title[:30]}...")
        
        insights = get_asta_insights(title, location, price)
        loc_context = loc_intel.get_location_context(location)
        
        if "High Flood Risk" in loc_context['risks']:
            insights['investment_vibe'] = f"⚠️ FLOOD ZONE ALERT. {insights.get('investment_vibe', '')}"

        # Clean raw data of NaNs
        raw_dict = row.drop(['clean_title', 'clean_address', 'fingerprint']).to_dict()
        raw_dict = clean_nan(raw_dict)

        item = {
            "id": str(uuid.uuid4()), # <--- FORCE NEW ID
            "url": listing_id,      
            "title": title,
            "price": float(str(price).replace(',','')) if str(price).replace(',','').replace('.','').isdigit() else 0,
            "location": location,
            "source": "csv_import",
            "insight_cache": insights,
            "location_intel": loc_context,
            "insight_last_updated": datetime.now().isoformat(),
            "last_seen_at": datetime.now().isoformat(),
            "raw_data": raw_dict
        }

        try:
            # We use a manual check-then-write approach to avoid Upsert errors with Constraints
            # 1. Check existence
            exists = False
            try:
                res = supabase.table("market_listings").select("url").eq("url", listing_id).execute()
                exists = len(res.data) > 0
            except: pass
            
            # 2. Write
            if exists:
                # Update (remove ID from payload so we don't overwrite it)
                update_payload = {k:v for k,v in item.items() if k != 'id'}
                supabase.table("market_listings").update(update_payload).eq("url", listing_id).execute()
            else:
                supabase.table("market_listings").insert(item).execute()
                
            enriched_count += 1
            # db_fingerprints.add(fingerprint) # Update local cache
        except Exception as e:
             print(f"   ❌ Save Error: {e}") # <--- NOW WE SEE ERRORS
             
        time.sleep(1.2) 

    print(f"✅ Done! Successfully enriched {enriched_count} properties.")

if __name__ == "__main__":
    main()
