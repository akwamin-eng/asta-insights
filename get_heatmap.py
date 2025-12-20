import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def fetch_heatmap():
    print("🔥 Fetching Accra Market Heatmap...")
    
    # Query the view we just created
    res = supabase.table("neighborhood_heatmap").select("*").order("heat_index", desc=True).execute()
    
    if not res.data:
        print("❌ No heatmap data found.")
        return

    print(f"{'Location':<20} | {'Heat Index':<10} | {'Sentiment':<10} | {'Vibe'}")
    print("-" * 65)
    
    for row in res.data:
        heat = row['heat_index']
        # Add visual indicator
        color = "🟢" if heat > 70 else "🟡" if heat > 40 else "🔴"
        
        print(f"{row['location']:<20} | {heat:<10} | {row['sentiment_score']:<10.2f} | {color} {row['key_phrases'][0] if row['key_phrases'] else 'Quiet'}")

if __name__ == "__main__":
    fetch_heatmap()
