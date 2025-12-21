import os
from google import genai
from google.genai import types
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize the new GenAI Client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_embedding(text):
    """Generates a 768-dim embedding using the new Gemini SDK."""
    try:
        # The new SDK syntax for embeddings
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                title="Real Estate Listing"
            )
        )
        # The new response object structure
        return result.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return None

def update_embeddings():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    print("🧠 Scanning for listings without embeddings...")
    
    # REMOVED 'description' from the select since it doesn't exist
    response = supabase.from_('market_listings').select('id, title, location, price').is_('embedding', 'null').limit(50).execute()
    listings = response.data

    if not listings:
        print("✅ All listings have embeddings.")
        return

    print(f"Processing {len(listings)} listings...")

    for item in listings:
        # Construct content from available fields
        content = f"Title: {item['title']}. Location: {item['location']}. Price: {item['price']}"
        
        vector = generate_embedding(content)
        
        if vector:
            # Update Supabase
            supabase.from_('market_listings').update({'embedding': vector}).eq('id', item['id']).execute()
            print(f"  ✨ Embedded: {item['title'][:30]}...")
        else:
            print(f"  ❌ Failed to embed: {item['id']}")

if __name__ == "__main__":
    update_embeddings()
