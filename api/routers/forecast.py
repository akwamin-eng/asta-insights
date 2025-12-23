from fastapi import APIRouter
from api.utils import supabase
import pandas as pd
import numpy as np

router = APIRouter(prefix="/forecast", tags=["Phase 2: Predictive Pulse"])

@router.get("/pulse")
async def get_market_pulse():
    # 1. Fetch live data
    properties = supabase.table("properties").select("*").execute().data
    news = supabase.table("news_articles").select("*").execute().data
    
    if not properties or not news:
        return {"message": "Insufficient data for forecasting"}

    # 2. Convert to DataFrames for analysis
    prop_df = pd.DataFrame(properties)
    news_df = pd.DataFrame(news)

    # 3. Correlation Logic: Infrastructure & Sentiment
    hotspots = []
    
    # Analyze news for 'Infrastructure' or 'Expansion' signals
    infra_keywords = ['road', 'construction', 'expansion', 'airport', 'infrastructure']
    
    for _, article in news_df.iterrows():
        title_lower = article['title'].lower()
        locations = article.get('related_locations', [])
        
        # Determine multiplier based on sentiment and keywords
        multiplier = 1.05 # Baseline 5% growth
        if any(kw in title_lower for kw in infra_keywords):
            multiplier += 0.15 # Add 15% infrastructure premium
        
        # Factor in sentiment (if news is negative, multiplier drops)
        multiplier += (article['sentiment_score'] * 0.1)

        for loc in locations:
            # Predict for properties in this specific location
            avg_price = prop_df[prop_df['location'] == loc]['price'].mean() if loc in prop_df['location'].values else 0
            
            hotspots.append({
                "location": loc,
                "growth_index": round(multiplier, 2),
                "signal_source": article['source'],
                "predicted_appreciation": f"{round((multiplier - 1) * 100, 1)}%",
                "confidence": "High" if article['sentiment_score'] != 0 else "Medium",
                "anchor_news": article['title']
            })

    # 4. Remove duplicates and return top hotspots
    pulse_results = pd.DataFrame(hotspots).drop_duplicates(subset=['location']).to_dict('records')
    
    return {
        "market_status": "Bullish" if news_df['sentiment_score'].mean() > 0 else "Cautious",
        "top_hotspots": pulse_results
    }
