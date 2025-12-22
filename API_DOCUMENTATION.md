# 📘 Asta Insights API Documentation

**Version:** 2.5.0  
**Base URL (Local):** `http://localhost:8000`  
**Base URL (Production):** `https://asta-insights.onrender.com` (Example)

---

## 🚀 Quick Start
Asta's API is built on **FastAPI**. It includes an interactive dashboard where you can test endpoints directly in your browser.

* **View Interactive Docs:** [Go to `/docs`](http://localhost:8000/docs)
* **View JSON Schema:** [Go to `/openapi.json`](http://localhost:8000/openapi.json)

---

## 🔑 Core Endpoints

### 1. The Unified Table
**Endpoint:** `GET /properties/unified`

**Use Case:** Populating the main dashboard grid/list view.
This endpoint returns normalized data. It joins the raw listing with our AI Insight Cache (`v_property_details` view).

* **Features:**
    * Prices are normalized to numbers.
    * `roi_score` (0-10) is pre-calculated.
    * `investment_vibe` provides the AI's "One-Line Pitch".

### 2. Mapbox / Google Maps Heatmap
**Endpoint:** `GET /properties/geojson`

**Use Case:** Adding a data source to Mapbox GL JS.
This returns a standard **GeoJSON FeatureCollection**. You do not need to parse it.

**Frontend Example (Mapbox):**
```javascript
map.addSource('asta-properties', {
  type: 'geojson',
  data: '[https://api.asta.com/properties/geojson](https://api.asta.com/properties/geojson)' // Point directly to API
});

map.addLayer({
  'id': 'points',
  'type': 'circle',
  'source': 'asta-properties',
  'paint': {
    'circle-color': [
      'interpolate', ['linear'], ['get', 'roi_score'],
      0, '#ff0000',  // Red (Bad ROI)
      10, '#00ff00'  // Green (Good ROI)
    ]
  }
});

### 7. AI-Powered GPS Extraction (World Class)
**Endpoint:** `POST /utils/extract-gps`

**Use Case:** "Auto-fill Location" for Agent Uploads.
This is a **Dual-Engine** system:
1.  **Engine A (EXIF):** Checks for precise GPS coordinates hidden in the file metadata.
2.  **Engine B (Gemini Vision):** If metadata is missing, it sends the image to Gemini to recognize landmarks, street signs, and architecture to estimate the location.

**Payload:** `multipart/form-data` with `file` (image).

**Response (Success - EXIF):**
```json
{
  "found": true,
  "latitude": 5.603,
  "longitude": -0.187,
  "message": "Extracted from EXIF Metadata (High Precision)"
}
eof

### 8. Frontend Optimization Guide (Ghana Market)

#### WhatsApp Integration
The `/properties/unified` endpoint now returns a `whatsapp_link` field.
* **Usage:** Bind this directly to the "Contact Agent" button.
* **Behavior:** Opens WhatsApp with a pre-filled message including the Property Ref ID.

#### Low-Data Image Loading (Crucial)
To ensure the app is fast on mobile data, **do not** use raw image URLs.
Append these parameters to any Supabase Storage URL:
* **Thumbnail:** `?width=400&resize=cover&quality=60`
* **Full Screen:** `?width=800&quality=75`

### 9. Security (RLS)
The database tables are now protected by **Row Level Security**.
* **Public Access:** `SELECT` (Read) only.
* **Write Access:** Restricted to Backend Services (Service Role Key).

---

## 🚨 CRITICAL: Frontend Performance Standards (Must Read)

**Target Market Context:** Mobile data in Ghana is expensive, and latency varies. Asta must be "Data-First."
**Requirement:** **NEVER** render raw image URLs returned by the API.

### ⚡️ Image Optimization Strategy (Supabase Transformations)
The API returns raw high-res references (e.g., `.../house1.jpg`). You must transform these on the client side before rendering.

| View Type | Required Query Parameters | Target Size |
| :--- | :--- | :--- |
| **List/Grid Cards** | `?width=400&resize=cover&quality=60` | ~30KB |
| **Detail Hero Image** | `?width=800&resize=contain&quality=75` | ~120KB |
| **Map Markers** | `?width=64&height=64&resize=cover&quality=50` | ~5KB |

### ❌ WRONG (Do not do this)
```jsx
// 🔴 This loads a 5MB file and will burn user data quotas
<img src={property.image_url} />
✅ RIGHT (Do this)
JavaScript

// 🟢 This loads a 40KB file optimized for 4G networks
const optimize = (url, width) => `${url}?width=${width}&resize=cover&quality=60`;

<img src={optimize(property.image_url, 400)} alt={property.title} />
Why? Failing to implement this will result in 10s+ load times on 4G networks and immediate user churn.

