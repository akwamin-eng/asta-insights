import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from fastembed import TextEmbedding
from google import genai  # <--- New Import

# 1. SETUP
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not GEMINI_API_KEY:
    print("❌ Error: Missing API Keys.")
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Gemini (New Client)
client = genai.Client(api_key=GEMINI_API_KEY)

print("🧠 Loading Vector Model (all-MiniLM-L6-v2)...")
embed_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def search_database(query_text):
    print(f"🔍 Searching database for: '{query_text}'...")
    try:
        # Generate vector
        query_vector = list(embed_model.embed([query_text]))[0].tolist()
        
        # Search Supabase
        response = supabase.rpc("search_market_listings", {
            "query_embedding": query_vector,
            "match_threshold": 0.50,
            "match_count": 8
        }).execute()
        
        return response.data
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return []

def ask_asta(user_question):
    listings = search_database(user_question)
    
    if not listings:
        print("🤖 Asta: I couldn't find any properties matching that description.")
        return

    # Prepare Context
    context_text = "Here are the most relevant properties found:\n"
    for item in listings:
        # Safe access to fields
        title = item.get('title', 'Unknown Property')
        loc = item.get('location', 'Unknown Location')
        price = item.get('price', 0)
        curr = item.get('currency', 'GHS') 
        src = item.get('source', 'System')
        
        context_text += f"- {title} in {loc}. Price: {curr} {price}. (Source: {src})\n"

    # Construct Prompt
    prompt = f"""
    You are Asta, a Real Estate AI for Ghana.
    Answer the user's question using ONLY the property listings below.
    
    If the price is 0, say "Price on request".
    Be concise, professional, and helpful.

    CONTEXT:
    {context_text}

    USER QUESTION:
    "{user_question}"
    """

    print("🤖 Asta is thinking...")
    try:
        # New Generation Syntax
        response = client.models.generate_content(
            model='gemini-2.0-flash',  # Trying the standard stable version for 2025
            contents=prompt
        )
        print("\n" + "="*50)
        print(response.text)
        print("="*50 + "\n")
    except Exception as e:
        print(f"⚠️ AI Error: {e}")

if __name__ == "__main__":
    print("👋 Hello! I am Asta. Ask me about properties (or type 'quit').")
    while True:
        try:
            q = input("You: ")
            if q.lower() in ['quit', 'exit']: break
            if q.strip(): ask_asta(q)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
