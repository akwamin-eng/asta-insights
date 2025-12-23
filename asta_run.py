import os
import sys
from scripts.enricher import get_asta_insights

def run_asta_pipeline():
    print("🚀 Starting Asta Pipeline...")
    # Your specific variable names are checked here
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY missing from environment.")
        sys.exit(1)
        
    print("🔍 Fetching properties and running AI enrichment...")
    # Add your DB fetch and loop logic here
    
if __name__ == "__main__":
    run_asta_pipeline()
