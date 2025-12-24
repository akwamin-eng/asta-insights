# �� Asta Insights API Reference (v4.2)

**Version:** 4.2 (Stable)  
**Status:** Live  
**Base URL:** `https://asta-insights.onrender.com`

---

## 🚀 Overview
Asta Insights is a modular AI backend designed for the Ghanaian real estate market. It combines **computer vision** (listing analysis), **market forecasting** (predictive pulse), and **omnichannel communication** (WhatsApp/Email).

### 🔑 Core Modules
1.  **Forecast (Predictive Pulse):** AI-driven appreciation predictions.
2.  **Listings:** Property management & GPS extraction.
3.  **Agent:** LLM-based conversational interface.
4.  **WhatsApp:** Twilio-integrated communication bridge.
5.  **Engagement:** Marketing automation & feedback.

---

## 1. 🔮 Forecast Module (New in v4.2)
*The "Predictive Pulse" engine correlates infrastructure news with market sentiment to predict property value shifts.*

### `GET /forecast/pulse`
Returns a list of high-growth investment "hotspots" based on real-time news analysis.

**Response:**
```json
{
  "market_status": "Bullish",
  "top_hotspots": [
    {
      "location": "Oyibi",
      "growth_index": 1.26,
      "predicted_appreciation": "26.0%",
      "confidence": "High",
      "anchor_news": "Road construction begins in Oyibi..."
    }
  ]
}
2. 🏘️ Listings Module
Handles property data, image processing, and AI enrichment.

POST /listings/upload
Uploads a property image, extracts GPS data automatically, and generates an AI description.

Body: multipart/form-data (file: image)

Process: 1. Compresses image (JPEG optimization). 2. Extracts EXIF GPS data. 3. Generates "Vibe" and "ROI Score" via Gemini Flash. 4. Uploads to Supabase Storage.

GET /listings/map
Returns GeoJSON data for rendering all active properties on a frontend map (e.g., Google Maps or Leaflet).

3. 💬 WhatsApp Bridge
Manages two-way communication between users and the AI agent via Twilio.

POST /whatsapp/webhook
Endpoint for Twilio. Receives incoming SMS/WhatsApp messages.

Logic:

Text: routed to Gemini LLM for conversational response.

Image: routed to Vision API for property analysis ("What is this house worth?").

Audio: (Planned) Voice note transcription.

4. 📢 Engagement Module
Marketing automation and user retention tools.

POST /engagement/newsletter
Triggers a bulk email to subscribers using Resend.

Payload: {"subject": "Market Alert", "content": "..."}

Backend: Uses api.utils.send_marketing_email to deliver HTML content.

POST /engagement/feedback
Collects user feedback ratings (1-5 stars) and stores them in Supabase for QA analysis.

5. 🛠️ Utilities (System)
Shared tools available via API for debugging or standalone use.

POST /utils/extract-gps
Standalone tool to test if an image contains readable location data.

Response: {"found": true, "latitude": 5.6037, "longitude": -0.1870}

🏗️ Architecture Notes
AI Engine: Google Gemini 1.5 Flash (via google-genai Unified SDK).

Database: Supabase (PostgreSQL).

Storage: Supabase Storage (Bucket: properties).

Geolocation: Google Maps API (Reverse Geocoding).

CI/CD: GitHub Actions (Daily Cron: News Scraping & Forecasting).

