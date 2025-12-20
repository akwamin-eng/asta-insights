import json
import re
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = "meqasa_master_dump.json"
OUTPUT_FILE = "meqasa_ready_for_db.json"

def clean_price_data(price_str):
    """Parses '$ 150,000' or 'GHc 5,000' -> (150000, 'USD')"""
    if not price_str or "request" in price_str.lower():
        return 0, "N/A"
    
    currency = "GHS"
    if "$" in price_str or "USD" in price_str:
        currency = "USD"
    
    clean_digits = re.sub(r'[^\d]', '', price_str)
    try:
        amount = int(clean_digits)
    except ValueError:
        amount = 0
    return amount, currency

def extract_beds_from_title(title):
    """Fallback: Finds '4 bedroom' or '3 bed' in the title string"""
    match = re.search(r'(\d+)\s*(?:bed|bd|bedroom)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0

def run_processing():
    print(f"📂 Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print("❌ File not found. Run the harvester first.")
        return

    processed_records = []
    
    print(f"⚙️  Processing {len(raw_data)} records...")
    
    for item in raw_data:
        title = item.get('title', 'Property').strip()
        location = item.get('location', 'Unknown Location').strip()
        
        # 1. Clean Price
        price_val, currency = clean_price_data(item.get('price'))
        
        # 2. Smart Bed Extraction
        beds = item.get('beds', '0')
        # If scraper returned 0 or non-numeric, try extracting from title
        if not str(beds).isdigit() or int(beds) == 0:
            beds = extract_beds_from_title(title)
        else:
            beds = int(beds)

        # 3. Construct Rich Embedding Text
        # We ensure no redundancy (e.g., don't say "Located in Osu" if title is "House in Osu")
        text_for_embedding = f"{title}. Located in {location}. Features {beds} bedrooms. Price: {price_val} {currency}."

        # 4. Create Golden Record
        record = {
            "id": item['id'], 
            "values": [], # Placeholder
            "metadata": {
                "source": "Meqasa",
                "title": title,
                "price": price_val,
                "currency": currency,
                "location": location,
                "url": item['url'],
                "beds": beds,
                "scraped_date": item.get('scraped_at', datetime.now().isoformat())
            },
            "_text_to_embed": text_for_embedding 
        }
        
        processed_records.append(record)

    # Save
    with open(OUTPUT_FILE, "w") as f:
        json.dump(processed_records, f, indent=2)

    print("\n" + "="*50)
    print(f"🎉 FIXED & PROCESSED!")
    print(f"💾 Saved {len(processed_records)} records to: {OUTPUT_FILE}")
    print("="*50)
    
    # Validation Preview
    if processed_records:
        print("Sample Record (Check 'beds' field):")
        print(json.dumps(processed_records[0], indent=2))

if __name__ == "__main__":
    run_processing()
