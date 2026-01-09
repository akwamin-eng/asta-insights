import { useState, useEffect } from "react";
import { supabase } from "../lib/supabase";
import { getRegionForLocation, type RegionName } from "../lib/regions";

interface ZoneStat {
  name: string;
  count: number;
  avgPrice: number;
  demandScore: number;
}

export interface MarketStats {
  activeListings: number; // Shows only Real LIVE Inventory
  verifiedCount: number; 
  avgPrice: number;       // Uses History + Live for accuracy
  medianPrice: number;
  avgRent: number;
  avgSale: number;
  zoneStats: ZoneStat[];
  lastUpdated: string;
}

export function useMarketStats(selectedRegion?: RegionName) {
  const [stats, setStats] = useState<MarketStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTitanIntel() {
      setLoading(true);

      try {
        // 1. FETCH "THE BRAIN" (Aggregated Historical + Live Data)
        const { data: titanData, error: titanError } = await supabase
          .from("analytics_market_pulse")
          .select("*");

        if (titanError) throw titanError;

        // 2. FETCH LIVE VERIFICATION COUNT (Real-time Audit)
        // We count actual rows in 'properties' that are active + verified (partner_id not null)
        let verifiedQuery = supabase
          .from("properties")
          .select("*", { count: "exact", head: true })
          .eq("status", "active")
          .not("partner_id", "is", null);

        const { count: verifiedCount } = await verifiedQuery;

        // 3. FILTER & AGGREGATE ON CLIENT
        const relevantPulse = selectedRegion
          ? titanData?.filter(
              (row) => getRegionForLocation(row.location_key) === selectedRegion
            ) || []
          : titanData || [];

        if (relevantPulse.length === 0) {
          setStats({
            activeListings: 0,
            verifiedCount: 0,
            avgPrice: 0,
            medianPrice: 0,
            avgRent: 0,
            avgSale: 0,
            zoneStats: [],
            lastUpdated: new Date().toISOString(),
          });
          return;
        }

        // 4. CALCULATE METRICS (Split Logic)
        let liveInventoryCount = 0;       // For "Net Assets" display (Live only)
        let totalStatisticalSamples = 0;  // For "Avg Price" math (Includes Intelligence Layer)
        let weightedPriceSum = 0;

        relevantPulse.forEach((row) => {
          // Count only currently ACTIVE assets for the dashboard counter
          liveInventoryCount += (row.live_count || 0);

          // Use EVERYTHING (History + Live) for robust pricing math
          totalStatisticalSamples += row.listing_count;
          weightedPriceSum += Number(row.avg_price) * row.listing_count;
        });

        const unifiedAvgPrice =
          totalStatisticalSamples > 0 
            ? Math.round(weightedPriceSum / totalStatisticalSamples) 
            : 0;

        // 5. BUILD ZONE LEADERBOARD
        // We prioritize zones with LIVE assets, but if inventory is low, 
        // we use the 'demandScore' (Intelligence) to populate the list so it isn't empty.
        const zoneStats: ZoneStat[] = relevantPulse
          .map((row) => ({
            name: row.location_key,
            count: row.live_count || 0, // Show Live Inventory count
            avgPrice: Number(row.avg_price),
            demandScore: Math.min(100, row.listing_count * 2), // Demand based on Intelligence volume
          }))
          // Sort: Primary = Inventory Count, Secondary = Market Activity (Intelligence)
          .sort((a, b) => b.count - a.count || b.demandScore - a.demandScore)
          .slice(0, 5);

        setStats({
          activeListings: liveInventoryCount, 
          verifiedCount: verifiedCount || 0,
          avgPrice: unifiedAvgPrice,          
          medianPrice: unifiedAvgPrice,
          avgSale: unifiedAvgPrice,
          avgRent: Math.round(unifiedAvgPrice * 0.008), // Estimated Yield
          zoneStats,
          lastUpdated: new Date().toISOString(),
        });
      } catch (err) {
        console.error("Error syncing with Titan Memory:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchTitanIntel();
  }, [selectedRegion]);

  return { stats, loading };
}
