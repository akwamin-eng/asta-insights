import requests
import os

# Render API URL
API_BASE_URL = "https://asta-insights.onrender.com"

def refresh_predictive_pulse():
    """
    Triggers the Asta Predictive Pulse API to correlate news sentiment 
    and infrastructure projects with property market growth.
    """
    print("🚀 Triggering Asta Predictive Pulse...")
    try:
        # Trigger the forecast logic via your API endpoint
        response = requests.get(f"{API_BASE_URL}/forecast/pulse")
        
        if response.status_code == 200:
            data = response.json()
            market_status = data.get('market_status', 'Unknown')
            hotspots = data.get('top_hotspots', [])
            
            print(f"✅ Pulse Updated Successfully.")
            print(f"📊 Current Market Sentiment: {market_status}")
            
            if hotspots:
                top_spot = hotspots[0]
                print(f"🔥 Prime Growth Spot: {top_spot.get('location')}")
                print(f"📈 Predicted Appreciation: {top_spot.get('predicted_appreciation')}")
            else:
                print("ℹ️ No new growth hotspots identified in this cycle.")
        else:
            print(f"❌ Failed to refresh pulse. HTTP Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error connecting to Asta API: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

if __name__ == "__main__":
    refresh_predictive_pulse()
