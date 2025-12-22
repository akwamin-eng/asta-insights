import os
import json
import re
from google import genai
from google.genai import types

def clean_json_text(text):
    """
    Cleans Gemini's output to ensure valid JSON.
    Removes markdown code blocks (```json ... ```) and whitespace.
    """
    if not text:
        return ""
    # Remove markdown code wrappers
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()

def get_asta_insights(title, location, price):
    """
    Sends property details to Gemini and returns structured investment analysis.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: Missing GOOGLE_API_KEY")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Act as a Real Estate Investment Expert for Ghana.
    Analyze this listing:
    - Title: "{title}"
    - Location: "{location}"
    - Price: {price} GHS

    Provide a JSON object with these exact keys:
    1. "investment_vibe": A short, punchy verdict (e.g., "Cash Flow King", "Overpriced", "Hidden Gem").
    2. "estimated_monthly_rent": A realistic monthly rent estimate in GHS (number only).
    3. "recommended_strategy": "Buy & Hold", "Flip", "Airbnb", or "Avoid".
    4. "roi_score": A score from 1-10 based on price-to-rent ratio.

    Output PURE JSON only. No markdown. No conversational text.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # 1. Get Text
        raw_text = response.text
        
        # 2. Clean Markdown
        clean_text = clean_json_text(raw_text)
        
        # 3. Parse
        data = json.loads(clean_text)
        return data

    except Exception as e:
        print(f"⚠️  Gemini Error for '{title}': {e}")
        # Uncomment the line below if you want to see exactly what broke it
        # print(f"   RAW RESPONSE: {response.text if 'response' in locals() else 'None'}")
        return None
