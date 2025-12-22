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
