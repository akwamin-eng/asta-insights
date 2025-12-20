# processing/llm_tasks/enricher.py
from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_property_enrichment(prop_title, address, price, econ_data):
    # 1. Generate Insight
    prompt = f"Assess investment value for {prop_title} in {address} at {price} GHS. Inflation is {econ_data['inflation']}%."
    insight_res = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    insight = insight_res.choices[0].message.content
    
    # 2. Generate Embedding
    emb_res = await client.embeddings.create(
        input=[f"{prop_title} {address} {insight}"],
        model="text-embedding-3-small"
    )
    return insight, emb_res.data[0].embedding