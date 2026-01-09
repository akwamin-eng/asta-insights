// src/lib/google.ts

const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

// Singleton Promise to track loading state
let googleMapsPromise: Promise<void> | null = null;

const loadGoogleMaps = (): Promise<void> => {
  if (googleMapsPromise) return googleMapsPromise;

  googleMapsPromise = new Promise((resolve, reject) => {
    // 1. Check if Google Maps AND the Places library are already available
    if (typeof window !== "undefined" && window.google?.maps?.places) {
      resolve();
      return;
    }

    // 2. Inject Script with ASYNC flag
    // We explicitly request '&libraries=places' here so we don't need importLibrary
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${API_KEY}&libraries=places&loading=async`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      // 3. SAFETY CHECK: Ensure the 'places' library is actually ready
      if (window.google?.maps?.places) {
        resolve();
      } else {
        // If the main script loaded but 'places' is lagging, poll for it
        let retries = 0;
        const checkInterval = setInterval(() => {
          retries++;
          if (window.google?.maps?.places) {
            clearInterval(checkInterval);
            resolve();
          } else if (retries > 50) {
            // Timeout after 5 seconds
            clearInterval(checkInterval);
            reject(new Error("Google Maps 'places' library failed to load."));
          }
        }, 100);
      }
    };

    script.onerror = (err) => {
      console.error("❌ Google Maps Load Error:", err);
      reject(err);
    };

    document.head.appendChild(script);
  });

  return googleMapsPromise;
};

// --- SERVICES ---

export const getAutocompleteService = async () => {
  await loadGoogleMaps();
  // Double-check just to be safe
  if (!window.google?.maps?.places) {
    throw new Error("Google Maps Places library is missing.");
  }
  return new google.maps.places.AutocompleteService();
};

export const getGeocoder = async () => {
  await loadGoogleMaps();
  return new google.maps.Geocoder();
};

// Singleton to avoid creating multiple dummy divs
let placesServiceInstance: google.maps.places.PlacesService | null = null;

export const getPlacesService = async () => {
  await loadGoogleMaps();

  if (!placesServiceInstance) {
    const ghostDiv = document.createElement("div");
    placesServiceInstance = new google.maps.places.PlacesService(ghostDiv);
  }

  return placesServiceInstance;
};
