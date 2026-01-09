import { useState, useEffect, useCallback } from 'react';
import { getAutocompleteService } from '../lib/google';

export function useGoogleAutocomplete() {
  const [service, setService] = useState<any>(null);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getAutocompleteService().then(s => setService(s));
  }, []);

  const getPredictions = useCallback(async (input: string) => {
    if (!input || input.length < 3 || !service) {
      setPredictions([]);
      return;
    }

    setLoading(true);
    try {
      service.getPlacePredictions(
        {
          input,
          componentRestrictions: { country: "gh" },
          // We don't restrict types strictly to (regions) to allow specific landmarks too
        },
        (results: any, status: any) => {
          setLoading(false);
          // Check for OK or ZERO_RESULTS status
          if ((status === "OK" || status === "ZERO_RESULTS") && results) {
            setPredictions(results);
          } else {
            setPredictions([]);
          }
        }
      );
    } catch (e) {
      console.error("Autocomplete Error:", e);
      setLoading(false);
      setPredictions([]);
    }
  }, [service]);

  return { predictions, getPredictions, loading, setPredictions };
}
