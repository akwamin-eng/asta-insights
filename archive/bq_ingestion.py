import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") # Your GCP Project ID
DATASET_ID = "asta_real_estate"                # Name of your dataset
TABLE_ID = "property_listings_raw"             # Name of your target table
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "asta-insights-data-certain-voyager")

def ingest_from_gcs():
    # Construct a BigQuery client object.
    client = bigquery.Client(project=PROJECT_ID)
    
    # Define the full table reference
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Configure the Load Job
    # We use Autodetect=True so BQ can figure out the schema from our JSON fields.
    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        # WRITE_APPEND adds new data to existing trends. 
        # WRITE_TRUNCATE would overwrite everything.
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND, 
    )

    # Use a wildcard to ingest all JSONs from all sites at once
    # This targets: raw/property_listings/[site]/[type]/[file].json
    uri = f"gs://{BUCKET_NAME}/raw/property_listings/*/*/*.json"

    print(f"📥 Starting BigQuery Load Job for: {uri}")
    
    try:
        load_job = client.load_table_from_uri(
            uri, table_ref, job_config=job_config
        )  # Make an API request.

        load_job.result()  # Waits for the job to complete.

        destination_table = client.get_table(table_ref)
        print(f"✅ Success! Table now has {destination_table.num_rows} total rows.")
        
    except Exception as e:
        print(f"❌ BigQuery Ingestion Failed: {e}")

if __name__ == "__main__":
    ingest_from_gcs()
