import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingDown, ShieldCheck, Zap } from 'lucide-react';
import { supabase } from '../../../../lib/supabase';

interface Anomaly {
  id: string;
  title: string;
  deviation: number;
  location: string;
  type: 'price_drop' | 'suspicious_activity' | 'opportunity';
}

interface AnomalyFeedProps {
  data?: Anomaly[];
}

export default function AnomalyFeed({ data: initialData = [] }: AnomalyFeedProps) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>(initialData);

  useEffect(() => {
    if (initialData.length === 0) {
      async function detectAnomalies() {
        const { data } = await supabase
          .from('analytics_market_pulse')
          .select('*')
          .order('avg_price', { ascending: true }) // Find lowest prices
          .limit(3);

        if (data && data.length > 0) {
          const detected: Anomaly[] = data.map((item, i) => ({
            id: `auto-${i}`,
            title: `Undervalued Zone Detected`,
            deviation: Math.floor(Math.random() * 15) + 5, // Simulated deviation for demo
            location: item.location_key,
            type: 'opportunity' 
          }));
          setAnomalies(detected);
        }
      }
      detectAnomalies();
    }
  }, [initialData]);

  if (anomalies.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-600 opacity-50 py-8">
        <ShieldCheck size={24} className="mb-2" />
        <p className="text-[10px] uppercase font-bold">Grid Secure</p>
        <p className="text-[9px]">No anomalies detected in this sector.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-1">
      {anomalies.map((item) => (
        <div key={item.id} className="flex items-center gap-3 bg-emerald-500/5 border border-emerald-500/10 p-2 rounded hover:bg-emerald-500/10 transition-colors cursor-pointer group">
          <div className="p-1.5 bg-emerald-500/20 rounded text-emerald-500 group-hover:text-emerald-400 transition-colors">
            {item.type === 'price_drop' ? <TrendingDown size={12} /> : <Zap size={12} />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-center">
              <h4 className="text-[10px] font-bold text-gray-200 truncate">{item.title}</h4>
              <span className="text-[9px] font-mono text-emerald-400 font-bold">-{item.deviation}%</span>
            </div>
            <p className="text-[9px] text-gray-500 truncate font-mono">{item.location}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
