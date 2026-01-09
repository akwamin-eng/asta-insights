import React, { useEffect, useState } from 'react';
import { MapPin } from 'lucide-react';
import { supabase } from '../../../../lib/supabase';

interface Neighborhood {
  name: string;
  count: number;
  avgPrice: number;
}

export default function NeighborhoodLeaderboard({ data: initialData = [] }: { data?: Neighborhood[] }) {
  const [leaderboard, setLeaderboard] = useState<Neighborhood[]>(initialData);

  useEffect(() => {
    // Connect to Brain if no manual data passed
    if (initialData.length === 0) {
      async function fetchIntel() {
        const { data } = await supabase
          .from('analytics_market_pulse')
          .select('location_key, listing_count, avg_price')
          .order('listing_count', { ascending: false })
          .limit(5);

        if (data) {
          const formatted = data.map(item => ({
            name: item.location_key,
            count: item.listing_count,
            avgPrice: item.avg_price
          }));
          setLeaderboard(formatted);
        }
      }
      fetchIntel();
    }
  }, [initialData]);

  if (leaderboard.length === 0) {
    return <div className="text-gray-500 text-xs p-4 text-center">Scanning market data...</div>;
  }

  return (
    <div className="overflow-x-auto h-full">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="text-[10px] text-gray-500 uppercase tracking-widest border-b border-white/10">
            <th className="pb-3 pl-2 w-10">#</th>
            <th className="pb-3">Neighborhood</th>
            <th className="pb-3 text-right">Vol</th>
            <th className="pb-3 text-right pr-2">Avg. Price</th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {leaderboard.map((hood, index) => (
            <tr key={index} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
              <td className="py-3 pl-2 text-gray-500 font-mono text-xs">{index + 1}</td>
              <td className="py-3 font-medium text-white flex items-center gap-2">
                <MapPin size={12} className={`
                    ${index === 0 ? 'text-amber-400' : index === 1 ? 'text-gray-300' : index === 2 ? 'text-orange-400' : 'text-gray-600'}
                `} />
                <span className="truncate max-w-[100px]">{hood.name}</span>
              </td>
              <td className="py-3 text-right text-gray-300 font-mono text-xs">
                {hood.count}
              </td>
              <td className="py-3 text-right pr-2 text-emerald-400 font-mono text-xs">
                ₵{hood.avgPrice.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
