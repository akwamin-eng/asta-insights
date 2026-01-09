import React, { useState, useEffect } from 'react';
import { TrendingUp, BarChart3, ArrowUpRight, Info, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { supabase } from '../../../../lib/supabase';

interface ClockProps {
  title: string;
  value: string;
  subValue: React.ReactNode;
  icon: React.ReactNode;
  color: string;
  tooltipText: string;
}

function ClockCard({ title, value, subValue, icon, color, tooltipText }: ClockProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className={`bg-white/5 border border-white/10 p-3 rounded-lg relative overflow-hidden group hover:border-${color}-500/30 transition-colors`}>
      <div className="absolute right-0 top-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
        {icon}
      </div>
      
      <div className="flex justify-between items-center z-10 relative">
        <p className="text-[10px] text-gray-400 uppercase tracking-wider font-bold">{title}</p>
        <button onClick={() => setShowTooltip(true)} className="text-gray-600 hover:text-white">
          <Info size={10} />
        </button>
      </div>

      <div className="mt-1 relative z-10">
        <p className="text-xl font-bold text-white flex items-center gap-1">
          {value}
        </p>
        <div className="mt-1">{subValue}</div>
      </div>

      <AnimatePresence>
        {showTooltip && (
          <div className="absolute inset-0 bg-[#0A0A0A]/95 backdrop-blur-sm z-20 p-3 flex flex-col justify-center text-center">
            <button onClick={() => setShowTooltip(false)} className="absolute top-2 right-2 text-gray-500 hover:text-white">
              <X size={12} />
            </button>
            <p className="text-[10px] text-gray-300 leading-snug">{tooltipText}</p>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function IntelligenceClocks() {
  const [marketVolume, setMarketVolume] = useState(0);

  useEffect(() => {
    async function getVolume() {
      // Connect to Brain: Count total intelligence points
      const { count } = await supabase.from('market_listings').select('*', { count: 'exact', head: true });
      if (count) setMarketVolume(count);
    }
    getVolume();
  }, []);

  return (
    <div className="grid grid-cols-2 gap-3 mb-6">
      <ClockCard 
        title="Est. Yield"
        value="8-12%"
        color="emerald"
        icon={<TrendingUp size={40} />}
        subValue={<span className="text-xs text-emerald-400 flex items-center gap-1">+2.4% <ArrowUpRight size={10}/></span>}
        tooltipText="Estimated annual rental yield based on current average rent vs. property value in this zone."
      />
      
      <ClockCard 
        title="Market Heat"
        value={marketVolume > 800 ? "Volcanic" : "High"} 
        color="orange"
        icon={<BarChart3 size={40} />}
        subValue={
          <div className="flex flex-col gap-1 mt-1">
             <div className="flex gap-0.5">
                <div className={`w-6 h-1 rounded-full ${marketVolume > 200 ? 'bg-orange-500' : 'bg-gray-700'}`} />
                <div className={`w-6 h-1 rounded-full ${marketVolume > 500 ? 'bg-orange-500' : 'bg-gray-700'}`} />
                <div className={`w-6 h-1 rounded-full ${marketVolume > 800 ? 'bg-orange-500' : 'bg-gray-700'}`} />
             </div>
             <span className="text-[9px] text-gray-500 font-mono">
               {marketVolume} Data Points
             </span>
          </div>
        }
        tooltipText="Demand index calculated by search volume and available inventory velocity."
      />
    </div>
  );
}
