import React, { useState } from 'react';
import { Crosshair, Layers, Filter, Shield, DollarSign, Map as MapIcon, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FieldControlsProps {
  onLocate: () => void;
  isLocating: boolean;
  onFilterChange: (type: 'all' | 'rent' | 'sale') => void;
  onLayerChange: (layer: 'standard' | 'price' | 'trust') => void;
}

export default function FieldControls({ onLocate, isLocating, onFilterChange, onLayerChange }: FieldControlsProps) {
  const [activeLayer, setActiveLayer] = useState<'standard' | 'price' | 'trust'>('standard');
  const [activeFilter, setActiveFilter] = useState<'all' | 'rent' | 'sale'>('all');
  const [showLayers, setShowLayers] = useState(false);

  const handleLayer = (layer: 'standard' | 'price' | 'trust') => {
    setActiveLayer(layer);
    onLayerChange(layer);
    setShowLayers(false);
  };

  const handleFilter = (filter: 'all' | 'rent' | 'sale') => {
    setActiveFilter(filter);
    onFilterChange(filter);
  };

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-end gap-3 z-[40] w-full max-w-md px-4 pointer-events-none">
      
      {/* 1. LOCATE ME (Left) */}
      <button 
        onClick={onLocate}
        className="pointer-events-auto w-12 h-12 bg-black/80 backdrop-blur-xl border border-white/20 rounded-full flex items-center justify-center text-emerald-500 shadow-lg hover:bg-emerald-500 hover:text-white transition-all active:scale-95"
      >
        {isLocating ? <Loader2 className="animate-spin" size={20} /> : <Crosshair size={20} />}
      </button>

      {/* 2. MAIN HUD (Center) */}
      <div className="pointer-events-auto flex-1 bg-black/80 backdrop-blur-xl border border-white/20 rounded-2xl p-1.5 flex justify-between shadow-2xl">
        {/* Filter Toggles */}
        <div className="flex gap-1 bg-white/5 rounded-xl p-1">
           <button 
             onClick={() => handleFilter('all')}
             className={`px-3 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${activeFilter === 'all' ? 'bg-gray-700 text-white shadow' : 'text-gray-400 hover:text-white'}`}
           >
             All
           </button>
           <button 
             onClick={() => handleFilter('sale')}
             className={`px-3 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${activeFilter === 'sale' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
           >
             Sale
           </button>
           <button 
             onClick={() => handleFilter('rent')}
             className={`px-3 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${activeFilter === 'rent' ? 'bg-orange-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
           >
             Rent
           </button>
        </div>
      </div>

      {/* 3. LAYERS (Right) */}
      <div className="pointer-events-auto relative">
        <AnimatePresence>
          {showLayers && (
            <motion.div 
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: -8, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.9 }}
              className="absolute bottom-full right-0 mb-2 bg-black/90 border border-white/20 rounded-xl overflow-hidden shadow-2xl min-w-[140px]"
            >
               <div className="p-2 space-y-1">
                 <div className="px-2 py-1 text-[9px] text-gray-500 uppercase font-bold tracking-wider">Map Intel Layer</div>
                 <button 
                   onClick={() => handleLayer('standard')}
                   className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-bold transition-all ${activeLayer === 'standard' ? 'bg-emerald-600/20 text-emerald-400' : 'text-gray-400 hover:bg-white/5'}`}
                 >
                   <MapIcon size={14} /> Standard
                 </button>
                 <button 
                   onClick={() => handleLayer('price')}
                   className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-bold transition-all ${activeLayer === 'price' ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:bg-white/5'}`}
                 >
                   <DollarSign size={14} /> Price Heatmap
                 </button>
                 <button 
                   onClick={() => handleLayer('trust')}
                   className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-bold transition-all ${activeLayer === 'trust' ? 'bg-purple-600/20 text-purple-400' : 'text-gray-400 hover:bg-white/5'}`}
                 >
                   <Shield size={14} /> Trust Radar
                 </button>
               </div>
            </motion.div>
          )}
        </AnimatePresence>

        <button 
          onClick={() => setShowLayers(!showLayers)}
          className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-95 border ${showLayers || activeLayer !== 'standard' ? 'bg-emerald-600 border-emerald-400 text-white' : 'bg-black/80 border-white/20 text-emerald-500'}`}
        >
          <Layers size={20} />
        </button>
      </div>

    </div>
  );
}
