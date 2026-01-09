import React from 'react';
import { Zap, Droplets, Shield, Wifi, Car, Waves } from 'lucide-react';

export const AMENITIES = [
  { id: 'pool', label: 'Pool', icon: <Waves size={12} /> },
  { id: 'generator', label: 'Generator', icon: <Zap size={12} /> },
  { id: 'security', label: '24/7 Security', icon: <Shield size={12} /> },
  { id: 'water', label: 'Water Tank', icon: <Droplets size={12} /> },
  { id: 'internet', label: 'Fiber', icon: <Wifi size={12} /> },
  { id: 'parking', label: 'Parking', icon: <Car size={12} /> },
];

interface VibeDeckProps {
  selected: string[];
  onToggle: (id: string) => void;
}

export default function VibeDeck({ selected, onToggle }: VibeDeckProps) {
  return (
    <div className="mt-3 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {AMENITIES.map((item) => (
        <button
          key={item.id}
          onClick={() => onToggle(item.id)}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition-all whitespace-nowrap border
            ${selected.includes(item.id) 
              ? 'bg-emerald-500 text-black border-emerald-500 shadow-lg shadow-emerald-500/20' 
              : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'}
          `}
        >
          {item.icon} {item.label}
        </button>
      ))}
    </div>
  );
}
