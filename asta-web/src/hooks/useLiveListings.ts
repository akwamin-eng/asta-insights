import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

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
  description?: string; 
  property_class?: string;
  type: "sale" | "rent";
  status?: "active" | "pending_review" | "sold" | "archived";
  cover_image_url?: string;
  images?: string[];
  owner_id?: string;
  owner?: any;
  boundary_geom?: any; 
  land_metadata?: {
    acres?: number;
    calculated_acres?: number;
    zoning?: string;
    title_type?: string;
    [key: string]: any;
  };
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
    fetchListings();

    const channel = supabase
      .channel("public:properties")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "properties" },
        (payload) => {
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
          status,
          location_name,
          location_accuracy,
          vibe_features,
          property_class, 
          type,
          cover_image_url,
          details,
          owner_id,
          source,
          features,
          boundary_geom,
          land_metadata
        `
        )
        .neq("status", "archived"); 

      if (error) throw error;

      const normalized = (data || []).map((p: any) => {
        // 🟢 OPTIMIZATION: Reduce Coordinate Precision to 6 decimals (~11cm)
        // This saves memory in the GeoJSON object
        const lat = p.lat ? Number(p.lat.toFixed(6)) : 0;
        const long = p.long ? Number(p.long.toFixed(6)) : 0;

        return {
          ...p,
          lat,
          long,
          property_class: p.property_class || "House",
          vibe_features: Array.isArray(p.features) ? p.features : [],
          images: p.cover_image_url ? [p.cover_image_url] : [],
          boundary_geom: p.boundary_geom,
          land_metadata: p.land_metadata,
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

  return { listings, loading, refresh: fetchListings };
}
