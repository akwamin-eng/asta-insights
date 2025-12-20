import json
import os
import re
import time
import sys
from typing import List
from pathlib import Path  # Add this
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# --- ROBUST CONFIG LOAD ---
# 1. Force find .env file relative to this script
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent  # Go up two levels to 'asta-insights'
env_path = project_root / ".env"

print(f"🔍 Looking for .env at: {env_path}")
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2. explicit Debug Check
if not SUPABASE_URL:
    print("❌ Error: SUPABASE_URL is missing. Check your .env file.")
    sys.exit(1)
if not SUPABASE_KEY:
    print("❌ Error: SUPABASE_SERVICE_ROLE_KEY is missing.")
    sys.exit(1)
if not OPENAI_API_KEY:
    print("❌ Error: OPENAI_API_KEY is missing.")
    sys.exit(1)

INPUT_FILE = "gpc_master_dump_2025.jsonl"
BATCH_SIZE = 20

# --- CLIENTS ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"🔥 Client Init Error: {e}")
    sys.exit(1)

# ... (Rest of the functions: clean_price, get_embeddings_batch, etc.) ...
# ... Copy the rest of the previous script here ...