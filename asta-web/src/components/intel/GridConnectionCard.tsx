import React from 'react';
import { Zap, Droplets, Wifi, MapPin } from 'lucide-react';

export default function GridConnectionCard({ locationName }: { locationName: string }) {
  // 🧠 Mock GIS Logic: In production, this would query a PostGIS layer of utility lines.
  // For now, we randomize slightly based on location name length to be deterministic.
  const isRemote = locationName.length > 15; 
  
  const powerDist = isRemote ? "0.8 km" : "On Site";
  const waterDist = isRemote ? "Borehole Req." : "GWCL Mains";
  const fiberDist = isRemote ? "4G Only" : "Fiber Ready";

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-5 hover:border-yellow-500/30 transition-colors">
      <h3 className="text-white font-bold text-sm flex items-center gap-2 mb-4">
        <Zap size={16} className="text-yellow-500" />
        Grid Infrastructure
      </h3>

      <div className="grid grid-cols-3 gap-2">
        <div className="bg-white/5 p-3 rounded-lg flex flex-col items-center text-center gap-2">
          <Zap size={18} className={powerDist === "On Site" ? "text-emerald-400" : "text-yellow-400"} />
          <div>
            <p className="text-[10px] text-gray-500 uppercase font-bold">Power</p>
            <p className="text-xs font-bold text-white">{powerDist}</p>
          </div>
        </div>

        <div className="bg-white/5 p-3 rounded-lg flex flex-col items-center text-center gap-2">
          <Droplets size={18} className={waterDist.includes("Mains") ? "text-blue-400" : "text-gray-400"} />
          <div>
            <p className="text-[10px] text-gray-500 uppercase font-bold">Water</p>
            <p className="text-xs font-bold text-white">{waterDist}</p>
          </div>
        </div>

        <div className="bg-white/5 p-3 rounded-lg flex flex-col items-center text-center gap-2">
          <Wifi size={18} className={fiberDist.includes("Fiber") ? "text-purple-400" : "text-gray-400"} />
          <div>
            <p className="text-[10px] text-gray-500 uppercase font-bold">Comms</p>
            <p className="text-xs font-bold text-white">{fiberDist}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
