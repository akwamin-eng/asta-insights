import { useState, useCallback } from 'react';
import { getPlacesService, getGeocoder } from '../lib/google';

export function useGooglePlaces() {
  const [loading, setLoading] = useState(false);

  // 1. Text Search (Legacy / Fallback)
  const searchPlace = useCallback(async (query: string) => {
    setLoading(true);
    try {
      const service = await getPlacesService();
      if (!service) return null;

      return new Promise<any>((resolve) => {
        const request = {
          query,
          fields: ['name', 'geometry', 'formatted_address'],
        };

        service.findPlaceFromQuery(request, (results: any, status: any) => {
          setLoading(false);
          if (status === 'OK' && results && results.length > 0) {
            resolve({
              name: results[0].name,
              address: results[0].formatted_address,
              location: {
                lat: results[0].geometry.location.lat(),
                lng: results[0].geometry.location.lng(),
              },
              viewport: results[0].geometry.viewport ? {
                northeast: {
                  lat: results[0].geometry.viewport.getNorthEast().lat(),
                  lng: results[0].geometry.viewport.getNorthEast().lng()
                },
                southwest: {
                  lat: results[0].geometry.viewport.getSouthWest().lat(),
                  lng: results[0].geometry.viewport.getSouthWest().lng()
                }
              } : null
            });
          } else {
            resolve(null);
          }
        });
      });
    } catch (error) {
      console.error("Search Error:", error);
      setLoading(false);
      return null;
    }
  }, []);

  // 2. Place Details (Robust - Uses Place ID)
  const getPlaceDetails = useCallback(async (placeId: string) => {
    setLoading(true);
    try {
      const service = await getPlacesService();
      if (!service) return null;

      return new Promise<any>((resolve) => {
        const request = {
          placeId: placeId,
          fields: ['name', 'geometry', 'formatted_address'],
        };

        service.getDetails(request, (place: any, status: any) => {
          setLoading(false);
          if (status === 'OK' && place) {
            resolve({
              name: place.name,
              address: place.formatted_address,
              location: {
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng(),
              },
              viewport: place.geometry.viewport ? {
                northeast: {
                  lat: place.geometry.viewport.getNorthEast().lat(),
                  lng: place.geometry.viewport.getNorthEast().lng()
                },
                southwest: {
                  lat: place.geometry.viewport.getSouthWest().lat(),
                  lng: place.geometry.viewport.getSouthWest().lng()
                }
              } : null
            });
          } else {
            console.warn("Place Details Failed:", status);
            resolve(null);
          }
        });
      });
    } catch (error) {
      console.error("Details Error:", error);
      setLoading(false);
      return null;
    }
  }, []);

  // 3. Geocoding (Address -> Lat/Lng)
  const reverseGeocode = useCallback(async (lat: number, lng: number) => {
    setLoading(true);
    try {
      const geocoder = await getGeocoder();
      return new Promise<string | null>((resolve) => {
        geocoder.geocode({ location: { lat, lng } }, (results: any, status: any) => {
          setLoading(false);
          if (status === 'OK' && results[0]) {
            resolve(results[0].formatted_address);
          } else {
            resolve(null);
          }
        });
      });
    } catch (error) {
      setLoading(false);
      return null;
    }
  }, []);

  return { searchPlace, getPlaceDetails, reverseGeocode, loading };
}
