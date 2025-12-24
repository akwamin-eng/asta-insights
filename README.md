# 🇬🇭 Asta Insights API (v4.2)

A modular AI backend designed for the Ghanaian real estate market.

## 🚀 Key Features

### Phase 1: Listings & Vision 🏘️
* **Image Uploads:** Optimizes photos and uploads to Supabase.
* **GPS Extraction:** Reads EXIF data to auto-locate properties.
* **Map Data:** Returns GeoJSON for frontend maps.

### Phase 2: Market Intelligence 📈
* **Predictive Pulse:** Scrapes news to find high-growth "hotspots".
* **Engagement:** Newsletter automation via Resend.

### Phase 3: Conversational Bridge 💬
* **WhatsApp Agent:** Uses **Gemini 2.0** to chat with users via Twilio.
* **Computer Vision:** Users can send photos of houses for instant analysis.
* **Lazy Listing:** Guided state machine allows listing properties entirely via chat.
* **Async Alerts:** Proactive notifications when listings go live.

## 🔗 Quick Links
* **Live Server:** [https://asta-insights.onrender.com](https://asta-insights.onrender.com)
* **Interactive Docs:** [https://asta-insights.onrender.com/docs](https://asta-insights.onrender.com/docs)
* **Market Pulse:** [https://asta-insights.onrender.com/forecast/pulse](https://asta-insights.onrender.com/forecast/pulse)

## 🛠️ Tech Stack
* **Framework:** Python FastAPI
* **Database:** Supabase (PostgreSQL)
* **AI:** Google Gemini 2.0 Flash
* **Messaging:** Twilio (WhatsApp) & Resend (Email)
* **Deployment:** Render

## 📝 Setup (Local)
1.  `python -m venv .venv`
2.  `source .venv/bin/activate`
3.  `pip install -r requirements.txt`
4.  Create `.env` file with keys.
5.  `uvicorn api.main:app --reload`
