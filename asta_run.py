import os
import sys

def run_asta_pipeline():
    print("🤖 Asta Autopilot: Starting Pipeline...")

    # 1. Verify Imports First (Fail Fast)
    try:
        from google import genai
        print("✅ Google GenAI SDK found.")
    except ImportError as e:
        print(f"❌ CRITICAL IMPORT ERROR: {e}")
        # Debugging: Print where python is looking
        print(f"Python Path: {sys.path}")
        sys.exit(1)

    # 2. Check Environment
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY missing.")
        sys.exit(1)

    # 3. Import Logic (Lazy import to avoid crashes before checks)
    from scripts.enricher import get_asta_insights
    
    print("🔍 Running Market Enrichment...")
    # Add your actual loop logic here or call the function
    # get_asta_insights(...)

    print("✅ Pipeline Step Complete.")

if __name__ == "__main__":
    run_asta_pipeline()
