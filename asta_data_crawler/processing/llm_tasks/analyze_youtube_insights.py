# processing/llm_tasks/analyze_youtube_insights.py
"""
Analyzes YouTube video content using Groq LLM to extract market insights.
"""
import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Any
from groq import AsyncGroq # Assuming Groq; install with `pip install groq`
from config.config import config # Import central config for API key

# Configure logger for this module (optional, but good practice)
import logging
logger = logging.getLogger(__name__)

# Initialize Groq Client using API key from central config
GROQ_API_KEY = config.GROQ_API_KEY
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in config. Please check your .env file.")

groq_client = AsyncGroq(api_key=GROQ_API_KEY)

async def analyze_youtube_insights_batch(video_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes a batch of YouTube video data (title, description, transcript) to generate insights.
    Uses Groq LLM for analysis.
    Returns a list of insight dictionaries corresponding to the input list.
    """
    if not video_data_list:
        return []

    print(f"🧠 Analyzing {len(video_data_list)} YouTube videos with Groq LLM...")

    analyzed_insights_list = []
    for i, video_data in enumerate(video_data_list):
        video_id = video_data.get("video_id", "unknown_video_id")
        title = video_data.get("title", "")
        text_for_nlp = video_data.get("text_for_nlp", "") # This includes title, description, and transcript

        if not text_for_nlp.strip():
            print(f"  ⚠️  Skipping video {video_id[:10]}... - No text available for analysis.")
            analyzed_insights_list.append({
                "hotspots": [],
                "cost_drivers": [],
                "infrastructure": [],
                "market_signals": [],
                "confidence": "low"
            })
            continue

        try:
            print(f"  📝 Analyzing video {i+1}/{len(video_data_list)}: {title[:50]}...")

            # --- Enhanced Prompt for Analysis ---
            prompt = f"""
You are a real estate intelligence analyst for Ghana.
Analyze the following YouTube video content to extract overall market sentiment and key trends for the Ghanaian real estate market.

Content:
{text_for_nlp}

Instructions:
Extract ONLY the following in a valid JSON object format.
DO NOT include any other text, markdown, explanations, or formatting.
Return ONLY the JSON object starting with '{{' and ending with '}}'.

{{
  "hotspots": ["list of emerging areas, e.g., 'East Legon Hills', 'Prampram', 'investing in Ghana']",
  "cost_drivers": ["list of cost factors, e.g., 'cement prices', 'land scarcity', 'rod iron']",
  "infrastructure": ["list of new projects, e.g., 'new airport', 'road expansion']",
  "market_signals": ["list of trends, e.g., 'rental yields compressing', 'demand rising', 'building in Ghana']",
  "confidence": "high|medium|low"
}}
JSON Object:
"""

            # --- Robust LLM Call with Retry ---
            max_retries = 2
            model_alias = config.DEFAULT_LLM_MODEL # Use from central config, e.g., "llama3-8b-8192"
            fallback_model_alias = "mixtral-8x7b-32768" # Known stable fallback

            analysis_result = {
                "hotspots": [],
                "cost_drivers": [],
                "infrastructure": [],
                "market_signals": [],
                "confidence": "low"
            } # Default result

            for attempt in range(max_retries + 1):
                try:
                    # Alternate between primary and fallback model on retry
                    if attempt == 0:
                        current_model_alias = model_alias
                    else:
                        current_model_alias = fallback_model_alias
                        print(f"    🔁 Retrying with fallback model: {current_model_alias}")

                    # Create model instance dynamically
                    # Add a tiny delay, sometimes helps with SDK stability
                    await asyncio.sleep(0.1)
                    
                    response = await groq_client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        model=current_model_alias,
                        temperature=config.LLM_TEMPERATURE, # Use from central config, e.g., 0.2
                        max_tokens=config.LLM_MAX_TOKENS, # Use from central config, e.g., 1000
                        top_p=0.95
                    )
                    
                    raw_response_text = response.choices[0].message.content.strip()
                    print(f"    ✅ Received LLM response for {video_id[:10]}...")

                    # --- Robust JSON Parsing ---
                    # Remove potential markdown code block wrapper (```json ... ```)
                    import re
                    json_match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            parsed_result = json.loads(json_str)
                            
                            # Validate keys and types
                            required_keys = ["hotspots", "cost_drivers", "infrastructure", "market_signals", "confidence"]
                            if all(key in parsed_result for key in required_keys):
                                # Ensure list fields are lists and contain strings
                                for key in ["hotspots", "cost_drivers", "infrastructure", "market_signals"]:
                                     if not isinstance(parsed_result.get(key, []), list):
                                          parsed_result[key] = [str(parsed_result[key])] if parsed_result.get(key) else []
                                     else:
                                          parsed_result[key] = [str(item) for item in parsed_result[key]]

                                # Ensure confidence is valid
                                conf = parsed_result.get("confidence", "low").lower()
                                if conf not in ["high", "medium", "low"]:
                                     parsed_result["confidence"] = "low"
                                else:
                                     parsed_result["confidence"] = conf

                                analysis_result = parsed_result
                                print(f"    🧠 Parsed insights for {video_id[:10]}... (Confidence: {parsed_result['confidence']})")
                                break # Break out of retry loop on success
                            else:
                                print(f"    ⚠️  LLM response JSON missing required keys for {video_id[:10]}...: {parsed_result}")
                        except json.JSONDecodeError as je:
                            print(f"    ⚠️  JSON parsing failed for {video_id[:10]}...: {je}")
                    else:
                         print(f"    ⚠️  No JSON object found in LLM response for {video_id[:10]}...: {raw_response_text[:100]}...")

                    # If parsing failed, retry
                    if attempt < max_retries:
                         print(f"      Retrying in 1 second...")
                         await asyncio.sleep(1)

                except Exception as e_call:
                    error_msg = str(e_call)
                    print(f"    ⚠️  LLM call failed (attempt {attempt + 1}/{max_retries + 1}) with {current_model_alias} for {video_id[:10]}...: {error_msg}")
                    if "unknown extension" in error_msg and attempt < max_retries:
                        print(f"      Retrying in 1 second with fallback model...")
                        await asyncio.sleep(1)
                    elif attempt < max_retries:
                         print(f"      Retrying in 1 second...")
                         await asyncio.sleep(1)
                    else:
                         print(f"    ❌  LLM call failed after {max_retries + 1} attempts for {video_id[:10]}....")
                         # analysis_result remains the default empty dict

            analyzed_insights_list.append(analysis_result)

        except Exception as e_video:
            print(f"  💥 Error analyzing video {video_id[:10]}...: {e_video}")
            # Append default insights on any failure for this video
            analyzed_insights_list.append({
                "hotspots": [],
                "cost_drivers": [],
                "infrastructure": [],
                "market_signals": [],
                "confidence": "low"
            })

        # Optional: Small delay between videos to be respectful to the LLM API
        if i < len(video_data_list) - 1:
             delay = 0.5 # seconds
             print(f"    ⏱️  Sleeping for {delay} seconds before next video...")
             time.sleep(delay)

    print(f"🧠 Completed analysis of {len(video_data_list)} YouTube videos.")
    return analyzed_insights_list

