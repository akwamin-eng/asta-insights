# explore_schema.py
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Load .env safely
load_dotenv(dotenv_path=Path('.') / '.env')

# Initialize client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("✅ Connected to Supabase!")

# List all tables in 'public' schema
try:
    tables_response = supabase.rpc("pg_tables").execute()
    public_tables = [
        row["tablename"] 
        for row in tables_response.data 
        if row["schemaname"] == "public"
    ]
    print("\n📋 Public tables:")
    for t in sorted(public_tables):
        print(f"  - {t}")
except Exception as e:
    print(f"⚠️ Could not fetch table list: {e}")
    print("Trying to query 'listings' directly...")

# Try to fetch 1 row from 'listings'
try:
    sample = supabase.table("listings").select("*").limit(1).execute()
    if sample.data:
        print(f"\n🔍 Sample row from 'listings' (showing keys):")
        print(list(sample.data[0].keys()))
        print("\nSample data:")
        print(sample.data[0])
    else:
        print("\n❗ 'listings' table exists but is empty.")
except Exception as e:
    print(f"\n❌ Error accessing 'listings' table: {e}")
    print("Possible causes:")
    print("  - Table doesn't exist")
    print("  - Row Level Security (RLS) blocks anon SELECT")
    print("  - Typo in table name")