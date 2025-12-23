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


---

## 🧠 Smart UX 2.0: Context & Conversation

### 1. Context-Aware Trust (`why_it_scored`)
The system now detects if a listing is for **Rent** or **Sale** and adjusts the "Trust Bullets" accordingly.

**Frontend Implementation:**
Simply render the strings in the `why_it_scored` array. The API handles the logic.

| Scenario | What the User Sees |
| :--- | :--- |
| **High ROI Sale** | `["💎 Rare High-Yield Asset", "📈 Strong Capital Appreciation"]` |
| **Luxury Rental** | `["🌟 Premium Lifestyle Area", "🔥 High Market Interest"]` |
| **Budget Rental** | `["💰 Competitive Rental Price", "⚖️ Fair Market Rent"]` |

> **Note:** We have replaced specific platform names (TikTok/Reddit) with "High Market Interest" to maintain a proprietary feel.

### 2. Human-Like Map Messaging (`human_message`)
The `/properties/nearby` endpoint now acts like a concierge. If it has to expand the search radius to find results, it generates a friendly explanation.

**New Payload (Request):**
```json
{
  "latitude": 5.603,
  "longitude": -0.187,
  "radius_km": 2.0,
  "location_name": "Osu" // Optional: Helps generate better messages
}
New Response Field:

human_message: A ready-to-display string explaining the result.

Frontend Implementation: Display human_message in a toast or summary bar above the map results.

Scenario A (Found nearby): "Found 12 homes within 2km."

Scenario B (Expanded Search): "We couldn't find the exact property in Osu, but we found similar listings 5km away."

Scenario C (Zero Results): "We couldn't find any listings in this area just yet."

3. Rent vs. Buy Intelligence
The API uses price thresholds (< 20k GHS) and title keywords ("Rent", "Lease") to automatically categorize listings. You do not need to manually filter these for the "Trust Bullets" to work; the backend handles the context switching.


## 📍 Advanced Location Parsing (Ghana Context)

The `/utils/extract-gps` endpoint is now context-aware for the Ghanaian market.
It accepts an image `file` AND an optional `text_hint` string.

**The "Waterfall" Logic:**
1.  **EXIF:** Checks for embedded GPS (Highest Accuracy).
2.  **Ghana Digital Address:** regex match for `GA-XXX-XXXX`.
3.  **Plus Codes:** Decodes `8FQM+57`.
4.  **AI Vision:** Scans the photo for painted addresses on walls or landmarks.

**Agent Use Case:**
> *"Agent snaps a photo of the gate (which has the Digital Address painted on it). Asta reads the text from the image and geolocates the property automatically."*


---

## 📍 Advanced Location Parsing (Ghana Context)

The `/utils/extract-gps` endpoint is now context-aware for the Ghanaian market.
It accepts an image `file` AND an optional `text_hint` string.

**The "Waterfall" Logic:**
1.  **EXIF:** Checks for embedded GPS (Highest Accuracy).
2.  **Ghana Digital Address:** Regex match for `GA-XXX-XXXX`. Resolves to coordinates via Google Geocoding.
3.  **Plus Codes:** Decodes `8FQM+57`.
4.  **AI Vision:** Scans the photo for painted addresses on walls or landmarks.

**Agent Use Case:**
> *"Agent snaps a photo of the gate. Asta reads 'GA-183-8192' and instantly places the pin on the map."*


---

## 📍 10. The Omni-Location Engine (Lazy Agent Protocol)

**Endpoint:** `POST /utils/extract-gps`

The `text_hint` field is now an **Omni-Input**. Agents do not need to select a format; the API automatically detects and parses the following formats in this order of priority:

| Priority | Format Detected | Example | Resolution Strategy |
| :--- | :--- | :--- | :--- |
| **1** | **Raw Coordinates** | `5.6037, -0.1870` | Direct parsing. Validates bounds (Ghana region). |
| **2** | **Ghana Digital Address** | `GA-182-6363` | 1. Checks internal **Cache** (fast).<br>2. Queries **GhanaPost Bridge**.<br>3. Fallback to **Google Geocoding**. |
| **3** | **Plus Codes** | `8FQM+57` | Decodes using OpenLocationCode library. |
| **4** | **Google Maps Link** | `maps.app.goo.gl/...` | Detects link pattern (Frontend should verify). |

### 🛡️ The Self-Healing Cache
The system now maintains a persistent `location_cache` table in Supabase.
* **First Query:** Slower (~2s) as it hits external APIs (SperixLabs/Google).
* **Second Query:** Instant (~50ms) as it serves from your own proprietary database.

### 📝 Integration Guide for Frontend
**Input Field Label:** "Location (Paste GPS, Ghana Post, or Coordinates)"
**Behavior:**
1. User uploads Image (System checks EXIF).
2. If EXIF fails, user types "GA-182-6363" into the text field.
3. System resolves address and autosets the map pin.

**Example Request:**
```bash
curl -X POST ... \
  -F "file=@photo.jpg" \
  -F "text_hint=5.560, -0.205"

---

## 🏠 11. Lazy Listing Publisher

**Endpoint:** `POST /listings/create`

The ultimate "One-Shot" endpoint. It takes raw inputs (images + minimal text) and performs the entire listing lifecycle automatically.

### ⚡️ What it automates:
1.  **GPS Extraction:** Scans EXIF data. If missing, parses the `location_hint` (Omni-Parser).
2.  **Reverse Geocoding:** Converts GPS coordinates into a human-readable neighborhood name (e.g., "East Legon").
3.  **Image Hosting:** Uploads all files to Supabase Storage (`/properties` bucket).
4.  **Database Record:** Creates the property entry with all derived data.

### 📥 Parameters (`multipart/form-data`)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `files` | `File[]` | **Yes** | One or more images (JPEG/HEIC). First image used for GPS. |
| `price` | `Float` | **Yes** | Numeric price value. |
| `currency` | `String` | No | Default: `GHS`. |
| `location_hint` | `String` | No | Any location format (Ghana Post, Plus Code, Lat/Lon) if EXIF is missing. |
| `description` | `String` | No | Optional description. If empty, title is auto-generated. |

### 📝 Example Usage
```bash
curl -X POST [https://api.asta/listings/create](https://api.asta/listings/create) \
  -F "files=@living_room.jpg" \
  -F "files=@kitchen.jpg" \
  -F "price=250000" \
  -F "location_hint=GA-182-6363"

---

## 🔍 12. Search Experience (UX Fixes)

These endpoints prevent "Dead Ends" in the user journey.

### 📍 Smart Radius Search (No Empty Maps)
**Endpoint:** `GET /listings/search`

Automatically expands the search radius if no properties are found nearby.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | Float | Required | User's latitude |
| `lon` | Float | Required | User's longitude |
| `radius_km` | Int | 5 | Starting search radius |

**Response:**
```json
{
  "results": [...],
  "radius_used": 15,
  "expanded": true,
  "message": "Found 3 properties within 15km"
}
🏷️ Trending Tags (No Blank Search Bar)
Endpoint: GET /listings/tags

Returns popular locations and vibes based on real database activity. Use these to render "Quick Filter" chips.

Response:

JSON

{
  "chips": ["📍 East Legon", "📍 Osu", "✨ Luxury", "✨ Coastal"]
}
