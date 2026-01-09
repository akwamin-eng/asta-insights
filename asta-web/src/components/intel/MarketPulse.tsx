import React, { useEffect, useState } from 'react';
import { Activity, TrendingUp, AlertCircle, Loader2 } from 'lucide-react';
import { supabase } from '../../lib/supabase';

export default function MarketPulse({ property }: { property: any }) {
  const [stats, setStats] = useState<{
    avgPrice: number;
    count: number;
    variance: number;
    loading: boolean;
  }>({ avgPrice: 0, count: 0, variance: 0, loading: true });

  useEffect(() => {
    fetchComparableData();
  }, [property.id]);

  async function fetchComparableData() {
    try {
      // 1. Define the "Comparable" criteria
      // Same Location Name (fuzzy match) AND Same Listing Type (Rent/Sale)
      // Note: In a real prod app, we'd use PostGIS for radius search
      const locationQuery = property.location_name.split(',')[0].trim(); 
      
      const { data, error } = await supabase
        .from('properties')
        .select('price')
        .eq('type', property.type) // Compare apples to apples
        .ilike('location_name', `%${locationQuery}%`) // Similar location
        .neq('id', property.id); // Exclude self

      if (error) throw error;

      if (!data || data.length === 0) {
        setStats({ avgPrice: 0, count: 0, variance: 0, loading: false });
        return;
      }

      // 2. Calculate Live Market Average
      // Normalize currencies if needed (assuming base GHS for now per seed)
      const total = data.reduce((sum, p) => sum + p.price, 0);
      const avg = Math.round(total / data.length);
      
      // 3. Calculate Variance
      const variance = Math.round(((property.price - avg) / avg) * 100);

      setStats({
        avgPrice: avg,
        count: data.length,
        variance,
        loading: false
      });

    } catch (err) {
      console.error("Market Pulse Error:", err);
      setStats(prev => ({ ...prev, loading: false }));
    }
  }

  // Formatting
  const fmt = (n: number) => '₵' + n.toLocaleString(undefined, { maximumFractionDigits: 0 });

  // Logic for Labels
  const getVerdict = (v: number) => {
    if (v > 20) return { label: 'Premium Price', color: 'text-red-400', bar: 'bg-red-500' };
    if (v < -20) return { label: 'Under Market', color: 'text-emerald-400', bar: 'bg-emerald-500' };
    return { label: 'Fair Value', color: 'text-blue-400', bar: 'bg-blue-500' };
  };

  const verdict = getVerdict(stats.variance);

  if (stats.loading) return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-4 mt-4 flex items-center justify-center h-24">
       <Loader2 className="animate-spin text-emerald-500" size={20} />
    </div>
  );

  // Fallback if not enough data
  if (stats.count < 3) return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-4 mt-4">
      <div className="flex items-center gap-2 text-gray-500 text-xs">
        <Activity size={14} />
        <span>Not enough data for market comparison.</span>
      </div>
    </div>
  );

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-4 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Activity size={14} className="text-emerald-500" /> Market Pulse
        </h3>
        <span className="text-[9px] text-gray-500 font-mono">
          VS. {stats.count} SIMILAR ASSETS
        </span>
      </div>

      {/* PRICE METER */}
      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-gray-400">Analysis Verdict:</span>
          <span className={`font-bold font-mono ${verdict.color}`}>{verdict.label}</span>
        </div>
        
        {/* Visual Bar */}
        <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-white/20 z-10" />
          <div 
            className={`absolute top-0 bottom-0 transition-all duration-500 ${verdict.bar}`}
            style={{ 
              left: '50%', 
              width: `${Math.min(Math.abs(stats.variance), 50)}%`,
              transform: stats.variance < 0 ? 'translateX(-100%)' : 'none'
            }} 
          />
        </div>
        
        <div className="flex justify-between mt-1 text-[9px] text-gray-600 font-mono">
          <span>-50%</span>
          <span>Avg</span>
          <span>+50%</span>
        </div>
      </div>

      {/* DATA GRID */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-white/5 rounded p-2 border border-white/5">
          <div className="text-[9px] text-gray-400 uppercase mb-1">Market Average</div>
          <div className="text-sm font-mono text-white font-bold">{fmt(stats.avgPrice)}</div>
          <div className="text-[9px] text-gray-500 mt-0.5">In this area</div>
        </div>

        <div className="bg-white/5 rounded p-2 border border-white/5">
          <div className="text-[9px] text-gray-400 uppercase mb-1 flex items-center gap-1">
             Variance <TrendingUp size={10} />
          </div>
          <div className={`text-sm font-mono font-bold ${stats.variance > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {stats.variance > 0 ? '+' : ''}{stats.variance}%
          </div>
          <div className="text-[9px] text-gray-500 mt-0.5">Vs. Average</div>
        </div>
      </div>

      {/* ADVISORY */}
      {Math.abs(stats.variance) > 25 && (
        <div className="mt-3 flex gap-2 items-start bg-blue-500/10 p-2 rounded border border-blue-500/20">
          <AlertCircle size={12} className="text-blue-400 shrink-0 mt-0.5" />
          <p className="text-[10px] text-blue-200 leading-tight">
            {stats.variance > 0 
              ? "Price is significantly higher than neighborhood average. Ensure finishes justify the premium." 
              : "Price is unusually low. Verify property condition or title authenticity."}
          </p>
        </div>
      )}
    </div>
  );
}
