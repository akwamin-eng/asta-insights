# main.py
import functions_framework
from google.cloud import secretmanager
import os

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/certain-voyager-403707/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

@functions_framework.http
def real_estate_pipeline(request):
    # Load secrets at runtime
    os.environ["SUPABASE_URL"] = get_secret("supabase-url")
    os.environ["SUPABASE_KEY"] = get_secret("supabase-key")
    
    from train_and_update import run_full_pipeline
    from scrape_ghana_listings import scrape_all
    
    try:
        scraped_df = scrape_all()
        run_full_pipeline(scraped_df=scraped_df)
        return "✅ Pipeline completed!", 200
    except Exception as e:
        print(f"💥 Error: {e}")
        return f"❌ Failed: {str(e)}", 500
        