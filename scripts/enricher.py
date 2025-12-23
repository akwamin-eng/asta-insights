import os
from google import genai
from google.genai import types

def get_asta_insights(image_bytes: bytes, price: float, location: str, listing_type: str):
    """
    Migrated to unified SDK. Uses GOOGLE_API_KEY env variable automatically.
    """
    client = genai.Client() # Picks up GOOGLE_API_KEY

    prompt = f"""
    Act as a professional real estate analyst. 
    Location: {location}, Price: {price}, Type: {listing_type}.
    Describe this property's unique vibe and investment ROI.
    Return ONLY JSON: {"vibe": "string", "score": number, "trust_bullets": ["string"]}
    """

    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                prompt
            ]
        )
        return response.text
    except Exception as e:
        print(f"AI Enrichment Error: {e}")
        return None
