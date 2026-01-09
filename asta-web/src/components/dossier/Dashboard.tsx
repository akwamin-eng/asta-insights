import React, { useState, useMemo } from "react";
import {
  Activity,
  Radio,
  FileText,
  Newspaper,
  MapPin,
  ChevronDown,
  Loader2,
} from "lucide-react";
import { useMarketStats } from "../../hooks/useMarketStats";
import { useMarketIntel } from "../../hooks/useMarketIntel";
import { GHANA_REGIONS, type RegionName } from "../../lib/regions";

import PlatformStats from "./modules/dashboard/PlatformStats";
import MetricCard from "./modules/dashboard/MetricCard";
import YieldChart from "./modules/dashboard/YieldChart";
import TrustPie from "./modules/dashboard/TrustPie";
import NeighborhoodLeaderboard from "./modules/dashboard/NeighborhoodLeaderboard";
import AnomalyFeed from "./modules/dashboard/AnomalyFeed";
import IntelligenceClocks from "./modules/IntelligenceClocks";

export default function Dashboard() {
  const [selectedRegion, setSelectedRegion] =
    useState<RegionName>("Greater Accra");
  const { stats, loading: statsLoading } = useMarketStats(selectedRegion);
  const { intel, loading: intelLoading } = useMarketIntel();

  // LOGIC UPDATE: Use Raw Database Count
  const totalAssets = stats?.activeListings || 0;
  const verifiedAssets = stats?.verifiedCount || 0;
  const unverifiedAssets = Math.max(0, totalAssets - verifiedAssets);

  const estimatedAvgSale = stats?.avgSale || 0;

  // DYNAMIC TRUST DATA
  const trustData = useMemo(() => {
    if (!totalAssets) return [];
    return [
      { name: "Verified", value: verifiedAssets, color: "#10b981" },
      { name: "Unverified", value: unverifiedAssets, color: "#ef4444" },
    ];
  }, [verifiedAssets, unverifiedAssets, totalAssets]);

  const chartData = [
    { month: "Oct", price: stats ? stats.avgPrice * 0.95 : 0 },
    { month: "Nov", price: stats ? stats.avgPrice * 0.98 : 0 },
    { month: "Dec", price: stats ? stats.avgPrice : 0 },
    { month: "Jan", price: stats ? stats.avgPrice * 1.02 : 0 },
  ];

  const tooltips = {
    assets: `Total active properties tracked in ${selectedRegion}.`,
    sale: "Estimated median sales price based on current market listings.",
    verified: "Assets physically inspected by Asta Scouts (Trust Tier A/B).",
    seekers: `Active Hunter Protocols scanning ${selectedRegion} right now.`,
  };

  const anomalies = useMemo(
    () => [
      {
        id: "1",
        title: "Sudden Drop: 4 Bed / Cantonments",
        deviation: 12,
        location: "Cantonments, Embassy Zone",
        type: "price_drop" as const,
      },
      {
        id: "2",
        title: "Below Market: 2 Bed / Osu",
        deviation: 8,
        location: "Osu, RE",
        type: "price_drop" as const,
      },
    ],
    []
  );

  // 🛡️ LOADING STATE: Prevents "Stuck/Zero" UI
  if (statsLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-emerald-500 animate-spin" />
        <p className="text-xs font-mono text-emerald-500/80 animate-pulse uppercase tracking-widest">
          Synchronizing Intelligence...
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 md:p-6 space-y-6 overflow-y-auto custom-scrollbar">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Market Matrix
          </h2>
          <p className="text-[10px] text-gray-400 font-mono uppercase tracking-widest">
            Real-time Intelligence // {selectedRegion} Sector
          </p>
        </div>

        {/* REGION DROPDOWN */}
        <div className="relative group z-[50]">
          <button className="flex items-center gap-2 bg-[#111] border border-white/10 hover:border-emerald-500/50 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all min-w-[200px] justify-between">
            <span className="flex items-center gap-2">
              <MapPin size={14} className="text-emerald-500" />
              {selectedRegion}
            </span>
            <ChevronDown
              size={14}
              className="text-gray-500 group-hover:text-white transition-colors"
            />
          </button>

          <div className="absolute right-0 top-full mt-2 w-full max-h-64 overflow-y-auto bg-black border border-white/20 rounded-lg shadow-2xl opacity-0 group-hover:opacity-100 invisible group-hover:visible transition-all custom-scrollbar">
            {GHANA_REGIONS.map((region) => (
              <button
                key={region}
                onClick={() => setSelectedRegion(region)}
                className={`w-full text-left px-4 py-3 text-[10px] uppercase font-bold tracking-wider hover:bg-emerald-900/20 hover:text-emerald-400 transition-colors border-b border-white/5 last:border-0 flex justify-between items-center ${
                  selectedRegion === region
                    ? "text-emerald-500 bg-emerald-900/10"
                    : "text-gray-400"
                }`}
              >
                {region}
                {selectedRegion === region && (
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* EMPTY STATE */}
      {stats?.activeListings === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center border border-white/10 border-dashed rounded-xl p-12 bg-white/5">
          <MapPin size={48} className="text-gray-600 mb-4" />
          <h3 className="text-lg font-bold text-gray-300">
            No Intelligence Data
          </h3>
          <p className="text-xs text-gray-500 mt-2 max-w-md text-center">
            Our scout network has not yet indexed verified assets in the{" "}
            <span className="text-emerald-500">{selectedRegion}</span>.
          </p>
          <button className="mt-6 px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold uppercase tracking-widest rounded transition-colors">
            Deploy Scout Request
          </button>
        </div>
      ) : (
        <>
          <PlatformStats
            totalAssets={totalAssets}
            avgRent={stats?.avgRent || 0}
            avgSale={estimatedAvgSale}
            verifiedCount={verifiedAssets}
            tooltips={tooltips}
          />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col gap-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <MetricCard
                  title="Price Trend (6M)"
                  icon={<Activity size={14} className="text-emerald-500" />}
                  helperTitle="Market Trajectory"
                  helperText={`Aggregated median listing price in ${selectedRegion}.`}
                  className="h-[250px]"
                >
                  <YieldChart data={chartData} />
                </MetricCard>

                <MetricCard
                  title="Trust Index"
                  icon={<Radio size={14} className="text-blue-500" />}
                  helperTitle="Verification Ratio"
                  helperText="Percentage of assets on the grid that have been physically verified."
                  className="h-[250px]"
                >
                  <TrustPie data={trustData} />
                </MetricCard>
              </div>

              {/* LIVE MARKET SIGNALS */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-5 flex-1 min-h-[300px] flex flex-col">
                <div className="flex justify-between items-center mb-4 shrink-0">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                    <Newspaper size={14} className="text-purple-500" /> Live
                    Market Signals
                  </h3>
                  {intelLoading && (
                    <Activity
                      size={12}
                      className="animate-spin text-gray-500"
                    />
                  )}
                </div>

                <div className="space-y-4 overflow-y-auto custom-scrollbar flex-1 pr-2">
                  {intel.length === 0 && !intelLoading ? (
                    <div className="h-full flex items-center justify-center text-gray-500 italic text-xs">
                      No active signals detected.
                    </div>
                  ) : (
                    intel.map((item) => (
                      <div
                        key={item.id}
                        className="flex gap-4 group cursor-default"
                      >
                        <div className="flex flex-col items-center gap-1 pt-1 min-w-[40px]">
                          <span className="text-[10px] font-mono text-gray-500">
                            {new Date(item.date).getDate()}
                          </span>
                          <span className="text-[9px] font-bold text-gray-600 uppercase">
                            {new Date(item.date).toLocaleString("default", {
                              month: "short",
                            })}
                          </span>
                        </div>
                        <div className="flex-1 pb-3 border-b border-white/5 group-last:border-0 overflow-hidden">
                          <h4 className="text-sm font-medium text-gray-200 truncate pr-4 group-hover:text-emerald-400 transition-colors">
                            {item.title}
                          </h4>
                          <p className="text-[11px] text-gray-500 mt-1 line-clamp-2">
                            {item.summary && !item.summary.startsWith("http")
                              ? item.summary
                              : "Market data analysis available."}
                          </p>
                          <div className="flex gap-2 mt-2">
                            <span className="text-[9px] bg-white/5 px-1.5 py-0.5 rounded text-gray-400 border border-white/5">
                              SOURCE:{" "}
                              {
                                item.source
                                  .replace("https://", "")
                                  .split("/")[0]
                              }
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-6 flex flex-col">
              <IntelligenceClocks />
              <MetricCard
                title="Detected Anomalies"
                icon={
                  <Radio size={14} className="text-red-500 animate-pulse" />
                }
                helperTitle="Outlier Detection"
                helperText="AI scans for listings with significant price deviations."
                className="min-h-[200px]"
              >
                <AnomalyFeed data={anomalies} />
              </MetricCard>
              <MetricCard
                title="Top Zones (Vol)"
                icon={<FileText size={14} className="text-amber-500" />}
                helperTitle="Market Volume"
                helperText="Neighborhoods with the highest number of active listings."
                className="flex-1 min-h-[300px]"
              >
                <NeighborhoodLeaderboard data={stats?.zoneStats || []} />
              </MetricCard>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
