import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def test_geojson_api():
    """
    Simulates a frontend request to the Asta GeoJSON API view.
    Verifies that the database is correctly transforming market insights 
    into a Mapbox-ready FeatureCollection.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return

    supabase = create_client(url, key)

    print("\n🛰️  Simulating Frontend API call to 'v_neighborhood_geojson'...")
    
    try:
        # Fetch the GeoJSON from the view
        # We use .limit(1) because the view aggregates everything into one row
        response = supabase.from_('v_neighborhood_geojson').select('*').execute()
        
        if response.data and len(response.data) > 0:
            # The view returns a column named 'jsonb_build_object' by default
            # based on our previous SQL definition
            geojson = response.data[0].get('jsonb_build_object', {})
            features = geojson.get('features', [])
            
            if features is None:
                print("⚠️  API returned an object, but 'features' is null. check SQL view.")
                return

            print(f"✅ Success! API returned {len(features)} neighborhoods.")
            
            # Spot check the first feature to ensure properties are mapped
            if len(features) > 0:
                sample = features[0]['properties']
                print("-" * 50)
                print(f"📍 Sample Neighborhood: {sample.get('location', 'Unknown')}")
                print(f"📈 ROI Score:          {sample.get('roi_score', 'N/A')}")
                print(f"😊 Sentiment:         {sample.get('sentiment', 'N/A')}")
                print(f"🏠 Listings:          {sample.get('listing_count', 'N/A')}")
                print("-" * 50)
            else:
                print("Empty Set: No features found in the collection.")
                
        else:
            print("❌ Error: API returned no data. Ensure 'market_insights' has geocoded rows.")
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

if __name__ == "__main__":
    test_geojson_api()
