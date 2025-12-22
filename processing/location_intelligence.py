import os
from supabase import create_client

class LocationIntelligence:
    def __init__(self):
        self.supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
        
        # 1. STATIC KNOWLEDGE BASE (Hard-coded "Truths")
        # In production, this would be a database table 'location_profiles'
        self.static_profiles = {
            "east legon": {
                "tags": ["Premium", "High Traffic", "Nightlife"],
                "risk_factors": ["High Rent Costs"],
                "growth_verdict": "Stable Premium"
            },
            "cantonments": {
                "tags": ["Diplomatic Zone", "Secure", "Luxury"],
                "risk_factors": [],
                "growth_verdict": "High Appreciation"
            },
            "kasoa": {
                "tags": ["Rapid Growth", "Affordable", "Commuter Town"],
                "risk_factors": ["High Flood Risk", "Heavy Traffic"],
                "growth_verdict": "Volatile but Promising"
            },
            "adabraka": {
                "tags": ["Central Business District", "Historic"],
                "risk_factors": ["Severe Flood Zone", "Noise Pollution"],
                "growth_verdict": "Commercial Only"
            },
            "oyibi": {
                "tags": ["Emerging", "New Infrastructure"],
                "risk_factors": ["Distance from Center"],
                "growth_verdict": "High Potential"
            },
            "airport residential": {
                "tags": ["Expat Favorite", "Luxury", "Quiet"],
                "risk_factors": ["Aircraft Noise"],
                "growth_verdict": "Stable Premium"
            }
        }

    def get_location_context(self, location_name):
        """
        Returns a rich context object for a given location.
        Combines Static Knowledge + Dynamic News Signals.
        """
        clean_loc = str(location_name).lower().strip().replace(',', '').replace('ghana', '').strip()
        
        # Default Profile
        context = {
            "verdict": "Neutral",
            "tags": [],
            "risks": [],
            "recent_signals": []
        }

        # 1. MATCH STATIC PROFILE (Fuzzy Match)
        for key, profile in self.static_profiles.items():
            if key in clean_loc:
                context["tags"] = profile["tags"]
                context["risks"] = profile["risk_factors"]
                context["verdict"] = profile["growth_verdict"]
                break
        
        # 2. FETCH DYNAMIC SIGNALS (From News Database)
        try:
            # We look for news articles where 'related_locations' contains this location
            # Note: Supabase text search would be better here, but doing a simple logical check for MVP
            res = self.supabase.table("news_articles").select("title, sentiment_score, summary").execute()
            
            for article in res.data:
                # Simple string matching for now (In prod: use a junction table locations <-> news)
                if clean_loc in str(article.get('related_locations', '')).lower() or clean_loc in article['title'].lower():
                    context["recent_signals"].append({
                        "headline": article['title'],
                        "sentiment": "Positive" if article['sentiment_score'] > 0 else "Negative",
                        "summary": article['summary']
                    })
                    
                    # Adjust verdict based on news?
                    if article['sentiment_score'] < -0.5:
                        context["risks"].append("Recent Negative Press")
                        
        except Exception as e:
            print(f"⚠️ Signal Fetch Error: {e}")

        return context

# Simple testing block
if __name__ == "__main__":
    li = LocationIntelligence()
    print("Testing Kasoa Context:", li.get_location_context("Kasoa"))
    print("Testing East Legon Context:", li.get_location_context("East Legon"))
