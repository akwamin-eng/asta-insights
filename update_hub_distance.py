import os
import math
from dotenv import load_dotenv
from supabase import create_client

# Load environment
if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define Main Hubs (KIA, Central Ridge, Tema Port)
HUBS = {
    "airport_dist": (5.6051, -0.1668),
    "central_dist": (5.5566, -0.1969),
    "port_dist": (5.6450, -0.0031)
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

def update_distances():
    print("📏 Calculating Distances to Key Hubs...")
    
    try:
        # Corrected syntax: .not_ is a property, not a function
        res = supabase.table("market_insights") \
            .select("location, latitude, longitude") \
            .not_.is_("latitude", "null") \
            .execute()
        
        if not res.data:
            print("❌ No geocoded data found in market_insights.")
            return

        for item in res.data:
            lat, lon = item['latitude'], item['longitude']
            loc_name = item['location']
            
            # Calculate distances using Haversine
            distances = {hub: haversine(lat, lon, coords[0], coords[1]) for hub, coords in HUBS.items()}
            
            # Update Database
            supabase.table("market_insights").update(distances).eq("location", loc_name).execute()
            print(f"   ✅ {loc_name}: {distances['airport_dist']}km to Airport, {distances['central_dist']}km to Central")
            
    except Exception as e:
        print(f"❌ Error during update: {e}")

if __name__ == "__main__":
    update_distances()
