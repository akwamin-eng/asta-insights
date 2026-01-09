import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

// Define the shape of our Property object
export interface Property {
  id: number;
  title: string;
  price: number;
  currency: "GHS" | "USD";
  lat: number;
  long: number;
  location_name: string;
  location_accuracy: "high" | "low";
  vibe_features: string | string[];
  description: string;
  property_class?: string;
  type: "sale" | "rent";
  cover_image_url?: string;
  images?: string[];
  owner?: any;
  // Flexible details object to handle various schema versions
  details?: {
    bedrooms?: number;
    bathrooms?: number;
    area_sqm?: number;
    [key: string]: any;
  };
}

export function useLiveListings() {
  const [listings, setListings] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Initial Fetch
    fetchListings();

    // 2. Realtime Subscription (The "Snappy" Part)
    const channel = supabase
      .channel("public:properties")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "properties" },
        (payload) => {
          console.log("⚡ Realtime Update detected:", payload);
          // When DB changes, immediately re-fetch to keep map in sync
          fetchListings();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  async function fetchListings() {
    try {
      // 1. Fetch data including the new 'image_urls' column
      const { data, error } = await supabase
        .from("properties")
        .select(
          `
          id,
          title,
          price,
          currency,
          lat,
          long,
          location_name,
          location_accuracy,
          vibe_features,
          description,
          description_enriched,
          property_class, 
          type,
          cover_image_url,
          image_urls, 
          property_images(url),
          details,
          owner_id,
          source,
          features
        `
        )
        .eq("status", "active"); // Only active pins

      if (error) throw error;

      // 2. Data Normalization & Fallbacks
      const normalized = (data || []).map((p: any) => {
        // Handle images: prioritize the array column (manual entry), fallback to relation
        let finalImages = p.image_urls || [];
        if (finalImages.length === 0 && p.property_images) {
          finalImages = p.property_images.map((i: any) => i.url);
        }

        return {
          ...p,
          // Fallback: If DB missing class, assume 'House' so it shows on map
          property_class: p.property_class || "House",

          // Ensure arrays are actually arrays
          vibe_features: Array.isArray(p.features) ? p.features : [],

          images: finalImages,

          details: p.details || { bedrooms: 1, bathrooms: 1 },
        };
      });

      setListings(normalized);
    } catch (err) {
      console.error("Error fetching live grid:", err);
    } finally {
      setLoading(false);
    }
  }

  // Return refresh so we can manually trigger it if needed
  return { listings, loading, refresh: fetchListings };
}
