# main.py
import functions_framework
from google.cloud import secretmanager
import os
import importlib.util
import sys
from datetime import datetime
import asyncio # Import asyncio (still needed if compute_index or other parts become async later, or just good practice now)

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/certain-voyager-403707/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Make the main pipeline function async in case other parts become async later
async def async_real_estate_pipeline(request):
    start_time = datetime.now()
    print(f"[{start_time.isoformat()}] INFO: Starting real_estate_pipeline execution (scraping disabled).")
    # Load secrets at runtime
    os.environ["SUPABASE_URL"] = get_secret("supabase-url")
    os.environ["SUPABASE_KEY"] = get_secret("supabase-key")

    # NEW: Import compute_index from run_pipeline.py
    # Dynamically load run_pipeline module
    spec = importlib.util.spec_from_file_location("run_pipeline", os.path.join(os.path.dirname(__file__), "run_pipeline.py"))
    run_pipeline_module = importlib.util.module_from_spec(spec)
    sys.modules["run_pipeline"] = run_pipeline_module # Optional: add to sys.modules for potential future imports
    spec.loader.exec_module(run_pipeline_module)
    compute_index = run_pipeline_module.compute_index

    from train_and_update import run_full_pipeline

    # Note: scrape_all is intentionally removed for now due to async/coroutine error
    # scraped_df = await scrape_all() # This line is removed
    scraped_df = None # Pass None to indicate no new data from scraping
    print(f"[{datetime.now().isoformat()}] INFO: Scrape step skipped. Proceeding with existing Supabase data only.")

    try:
        print(f"[{datetime.now().isoformat()}] INFO: Starting run_full_pipeline...")
        # Pass the (potentially None) scraped_df to run_full_pipeline
        processed_df = run_full_pipeline(scraped_df=scraped_df)
        print(f"[{datetime.now().isoformat()}] INFO: Completed run_full_pipeline.")

        # NEW: Call compute_index after run_full_pipeline
        print(f"[{datetime.now().isoformat()}] INFO: Starting compute_index...") # Log before calling
        compute_index()
        print(f"[{datetime.now().isoformat()}] INFO: Completed compute_index.") # Log after calling

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"[{end_time.isoformat()}] INFO: Pipeline completed successfully (scraping skipped)! Total duration: {duration}.")
        return "✅ Pipeline completed (scraping skipped)!", 200
    except Exception as e:
        error_time = datetime.now()
        print(f"[{error_time.isoformat()}] ERROR: Pipeline failed: {e}")
        # Print the full traceback for detailed debugging
        import traceback
        traceback.print_exc()
        return f"❌ Failed: {str(e)}", 500

# Wrap the async function for the sync HTTP trigger
@functions_framework.http
def real_estate_pipeline(request):
    # Run the async function synchronously
    return asyncio.run(async_real_estate_pipeline(request))

