import React, { useState } from "react";
import {
  Eye,
  MapPin,
  TrendingUp,
  Trash2,
  ExternalLink,
  ArrowRight,
  Info,
  X,
  Maximize2
} from "lucide-react";
import type { WatchlistItem } from "../../types/asta_types";
import { motion, AnimatePresence } from "framer-motion";

interface SmartWatchlistProps {
  items: WatchlistItem[];
  onRemove: (id: number) => void;
}

// --- INTERNAL: TOOLTIP ---
const WatchlistTooltip = () => (
  <div className="group relative inline-block ml-2 pointer-events-auto z-50">
    <Info size={14} className="text-emerald-500/50 hover:text-emerald-400 cursor-help transition-colors" />
    {/* FIX: Centered alignment (left-1/2) instead of right-aligned to prevent left-side bleeding */}
    <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-56 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none z-50">
      <div className="bg-black/95 backdrop-blur-xl border border-emerald-500/30 text-white text-[10px] p-3 rounded-lg shadow-[0_0_20px_rgba(16,185,129,0.2)]">
        <h4 className="font-bold text-emerald-400 uppercase tracking-wider mb-1 flex items-center gap-1">
          <TrendingUp size={10} /> Yield Tracker
        </h4>
        <p className="text-gray-400 leading-relaxed">
          Monitors selected assets for price fluctuations and status changes. Items here trigger <strong>High-Priority Alerts</strong> if market value drops below your threshold.
        </p>
        {/* Centered triangle arrow */}
        <div className="w-2 h-2 bg-black border-l border-t border-emerald-500/30 rotate-45 absolute left-1/2 -translate-x-1/2 -top-1"></div>
      </div>
    </div>
  </div>
);

export default function SmartWatchlist({
  items,
  onRemove,
}: SmartWatchlistProps) {
  const [selectedItem, setSelectedItem] = useState<WatchlistItem | null>(null);

  // EMPTY STATE
  if (!items || items.length === 0) {
    return (
      <div className="bg-[#111] border border-white/10 rounded-xl p-6 h-full flex flex-col items-center justify-center text-center relative overflow-hidden">
        {/* Header with Tooltip even when empty */}
        <div className="absolute top-4 left-4 flex items-center">
           <h3 className="text-xs font-bold text-gray-600 uppercase tracking-widest">Active Targets</h3>
           <WatchlistTooltip />
        </div>

        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-4 border border-white/5">
          <Eye size={20} className="text-gray-600" />
        </div>
        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest">
          Watchlist Empty
        </h3>
        <p className="text-[10px] text-gray-600 mt-2 max-w-[200px]">
          Tag assets with "High Interest" to track their yield velocity here.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl flex flex-col h-full overflow-hidden relative">
      
      {/* HEADER */}
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5 relative z-10">
        <h3 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2">
          <Eye size={12} className="text-emerald-500" />
          Active Targets ({items.length})
          <WatchlistTooltip />
        </h3>
      </div>

      {/* QUICK VIEW OVERLAY */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div 
            initial={{ opacity: 0, y: "100%" }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="absolute inset-0 z-20 bg-[#0A0A0A] flex flex-col"
          >
            <div className="relative h-48 bg-gray-800 shrink-0">
              <img 
                src={selectedItem.image_url} 
                alt={selectedItem.title} 
                className="w-full h-full object-cover opacity-80"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] to-transparent" />
              <button 
                onClick={() => setSelectedItem(null)}
                className="absolute top-3 right-3 bg-black/50 p-2 rounded-full text-white hover:bg-red-500/20 hover:text-red-500 transition-colors backdrop-blur-md"
              >
                <X size={16} />
              </button>
              <div className="absolute bottom-3 left-4 right-4">
                <div className="inline-block px-2 py-0.5 rounded bg-emerald-500 text-black text-[9px] font-black uppercase mb-1">
                  Tracking Active
                </div>
                <h2 className="text-lg font-bold text-white leading-tight">{selectedItem.title}</h2>
              </div>
            </div>
            
            <div className="p-6 flex-1 bg-gradient-to-b from-[#0A0A0A] to-black border-t border-white/10">
               <div className="flex justify-between items-center mb-6">
                 <div>
                   <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Current Valuation</p>
                   <p className="text-2xl font-mono text-emerald-400">₵{selectedItem.current_price.toLocaleString()}</p>
                 </div>
                 <div className="text-right">
                   <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Original Baseline</p>
                   <p className="text-sm font-mono text-gray-400 line-through">₵{selectedItem.original_price.toLocaleString()}</p>
                 </div>
               </div>

               <div className="space-y-3">
                 <div className="flex items-center gap-3 text-gray-400 text-xs p-3 rounded bg-white/5 border border-white/5">
                    <MapPin size={14} className="text-emerald-500" />
                    {selectedItem.location}
                 </div>
                 <div className="flex items-center gap-3 text-gray-400 text-xs p-3 rounded bg-white/5 border border-white/5">
                    <TrendingUp size={14} className="text-blue-500" />
                    Market Trend: Stable
                 </div>
               </div>

               <button 
                 onClick={() => onRemove(selectedItem.id)}
                 className="mt-6 w-full py-3 border border-red-500/30 text-red-500 hover:bg-red-500/10 rounded-lg text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-2 transition-colors"
               >
                 <Trash2 size={14} /> Stop Tracking
               </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* LIST */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2 relative z-0">
        {items.map((item) => {
          return (
            <div
              key={item.id}
              onClick={() => setSelectedItem(item)} // OPEN OVERLAY
              className="group bg-black/40 border border-white/5 hover:border-emerald-500/30 hover:bg-white/5 rounded-lg p-3 transition-all relative overflow-hidden cursor-pointer"
            >
              <div className="flex gap-3">
                {/* THUMBNAIL */}
                <div className="w-16 h-16 rounded bg-gray-800 flex-shrink-0 overflow-hidden relative border border-white/10 group-hover:border-emerald-500/50 transition-colors">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt="Asset"
                      className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-white/5">
                      <MapPin size={16} className="text-gray-600" />
                    </div>
                  )}
                </div>

                {/* DETAILS */}
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <h4 className="text-xs font-bold text-gray-200 truncate pr-4 group-hover:text-emerald-400 transition-colors">
                      {item.title}
                    </h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation(); // Don't trigger open
                        onRemove(item.id);
                      }}
                      className="text-gray-600 hover:text-red-500 transition-colors p-1"
                    >
                      <Trash2 size={10} />
                    </button>
                  </div>

                  <p className="text-[10px] text-gray-500 flex items-center gap-1 mt-1 font-mono">
                    <MapPin size={8} /> {item.location}
                  </p>

                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs font-mono text-emerald-400">
                      ₵{item.current_price.toLocaleString()}
                    </span>

                    {/* ACTIONS */}
                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="text-[9px] text-gray-500 uppercase font-bold flex items-center gap-1">
                        View Details <ArrowRight size={8} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
