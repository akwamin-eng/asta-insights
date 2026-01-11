import React, { memo } from "react";
import { 
  Search, Loader2, MapPin, Hash, LayoutDashboard, LogIn, X, GripVertical 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ListingCard from "./ListingCard";

interface MapSidebarProps {
  user: any;
  isMobileExpanded: boolean;
  setIsMobileExpanded: (v: boolean) => void;
  isSidebarHovered: boolean;
  setIsSidebarHovered: (v: boolean) => void;
  searchQuery: string;
  setSearchQuery: (v: string) => void;
  executeSearch: (v: string) => void;
  handleInput: (e: any) => void;
  isSearching: boolean;
  autocompleteLoading: boolean;
  suggestions: any[];
  showSuggestions: boolean;
  selectSuggestion: (item: any) => void;
  trendingTags: string[];
  filterType: string;
  setFilterType: (v: any) => void;
  minPrice: string;
  setMinPrice: (v: string) => void;
  maxPrice: string;
  setMaxPrice: (v: string) => void;
  applyPricePreset: (v: string) => void;
  handleDashboardReset: () => void;
  filteredListings: any[];
  selectedListing: any;
  setSelectedListing: (v: any) => void;
  openDossier: (v: any) => void;
  setAuthModalOpen: (v: boolean) => void;
  SIDEBAR_WIDTH: number;
  CONTENT_WIDTH: number;
  HANDLE_WIDTH: number;
}

// 🟢 MEMOIZE: This prevents the sidebar from re-rendering when the map moves
const MapSidebar = memo(({
  user,
  isMobileExpanded,
  setIsMobileExpanded,
  isSidebarHovered,
  setIsSidebarHovered,
  searchQuery,
  handleInput,
  executeSearch,
  isSearching,
  autocompleteLoading,
  suggestions,
  showSuggestions,
  selectSuggestion,
  trendingTags,
  filterType,
  setFilterType,
  minPrice,
  setMinPrice,
  maxPrice,
  setMaxPrice,
  applyPricePreset,
  handleDashboardReset,
  filteredListings,
  selectedListing,
  setSelectedListing,
  openDossier,
  setAuthModalOpen,
  SIDEBAR_WIDTH,
  CONTENT_WIDTH,
  HANDLE_WIDTH
}: MapSidebarProps) => {

  const sidebarVariants = {
    desktop: { x: isSidebarHovered ? 0 : -CONTENT_WIDTH, opacity: 1 },
    mobile: { y: isMobileExpanded ? 0 : "calc(100% - 100px)", opacity: 1 }
  };

  return (
    <motion.div
      onHoverStart={() => setIsSidebarHovered(true)}
      onHoverEnd={() => setIsSidebarHovered(false)}
      animate={window.innerWidth < 768 ? sidebarVariants.mobile : sidebarVariants.desktop}
      variants={sidebarVariants}
      transition={{ type: "spring", stiffness: 400, damping: 40 }}
      style={{ width: SIDEBAR_WIDTH }}
      className="absolute z-20 flex flex-row pointer-events-auto shadow-2xl md:left-0 md:top-0 md:bottom-0 inset-x-0 bottom-0 h-[80vh] md:h-full rounded-t-xl border-t border-white/20 md:rounded-none md:border-t-0 md:border-r"
    >
      <div style={{ width: CONTENT_WIDTH }} className="flex flex-col bg-asta-deep/95 backdrop-blur-md h-full shrink-0 overflow-hidden">
        
        {/* Mobile Handle */}
        <div className="md:hidden flex justify-center pt-2 pb-1 cursor-pointer" onClick={() => setIsMobileExpanded(!isMobileExpanded)}>
          <div className="w-12 h-1 bg-white/20 rounded-full mb-1" />
        </div>

        {/* Header & Search */}
        <div className="p-3 border-b border-white/10">
          <div className="flex items-center gap-3 mb-3">
            <img src="/logo.png" alt="Asta" className="h-6 w-auto object-contain" onError={(e: any) => (e.target.style.display = "none")} />
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> ASTA</h1>
            <div className="ml-auto">
              {user ? (
                <button onClick={() => openDossier("dashboard")} className="text-[9px] font-bold text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded hover:bg-emerald-500/10 transition-all flex items-center gap-1"><LayoutDashboard size={10} /> DOSSIER</button>
              ) : (
                <button onClick={() => setAuthModalOpen(true)} className="text-[9px] font-bold text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded hover:bg-emerald-500/10 transition-all flex items-center gap-1"><LogIn size={10} /> LOG IN</button>
              )}
            </div>
          </div>

          <div className="relative mb-3 z-50">
            <div className="search-bar-container relative">
              <input type="text" placeholder="Search..." value={searchQuery} onKeyDown={(e) => e.key === "Enter" && executeSearch(searchQuery)} onChange={handleInput} onFocus={() => suggestions.length > 0 && true} className="w-full bg-black/40 border border-white/10 rounded-lg py-1.5 pl-3 pr-8 text-xs text-white focus:outline-none focus:border-emerald-500/50 transition-all font-mono" />
              {isSearching || autocompleteLoading ? <Loader2 className="absolute right-3 top-2 text-emerald-500 w-3 h-3 animate-spin" /> : <Search className="absolute right-3 top-2 text-gray-500 w-3 h-3" />}
            </div>
            {showSuggestions && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-black/90 border border-white/10 rounded-lg shadow-xl overflow-hidden backdrop-blur-md">
                {suggestions.map((item: any, i: number) => <div key={i} onClick={() => selectSuggestion(item)} className="flex items-center gap-3 px-3 py-2 hover:bg-white/10 cursor-pointer transition-colors border-b border-white/5 last:border-0">{item.type === "location" ? <MapPin className="w-3 h-3 text-red-400" /> : <Hash className="w-3 h-3 text-emerald-400" />}<span className="text-xs text-gray-200">{item.value}</span></div>)}
              </div>
            )}
          </div>

          {/* Filters Area */}
          <div className={`${!isMobileExpanded && window.innerWidth < 768 ? "hidden" : "block"}`}>
            <div className="flex flex-wrap gap-1.5 mb-3 max-h-20 overflow-y-auto scrollbar-hide">
              {trendingTags.map((tag, i) => <button key={i} onClick={() => executeSearch(tag)} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[9px] text-asta-platinum hover:bg-emerald-500/20 transition-all">#{tag}</button>)}
            </div>
            <div className="flex gap-1 p-1 bg-white/5 rounded-lg mb-3">
              {["all", "sale", "rent"].map((type) => <button key={type} onClick={() => setFilterType(type)} className={`flex-1 py-1 text-[9px] uppercase font-bold tracking-wider rounded transition-all ${filterType === type ? "bg-emerald-500 text-black" : "text-gray-400 hover:bg-white/5"}`}>{type}</button>)}
            </div>
            <div className="mb-2">
              <div className="flex items-center gap-2 mb-2 bg-white/5 p-1 rounded-lg border border-white/10">
                <input type="number" placeholder="Min ₵" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} className="w-full bg-transparent text-white text-[10px] pl-2 py-1 focus:outline-none placeholder-gray-600" /><span className="text-gray-600 text-[10px]">-</span><input type="number" placeholder="Max ₵" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} className="w-full bg-transparent text-white text-[10px] pl-2 py-1 focus:outline-none placeholder-gray-600" />
              </div>
              <div className="flex gap-1">
                {["Budget", "Family", "Luxury"].map((label) => <button key={label} onClick={() => applyPricePreset(label)} className="flex-1 py-1 text-[8px] border border-white/10 rounded hover:bg-white/10 text-gray-400 transition-colors uppercase tracking-wide">{label}</button>)}
              </div>
            </div>
            <button onClick={handleDashboardReset} className="w-full mt-1 flex items-center justify-center gap-2 py-1.5 rounded border border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300 hover:border-red-500/50 transition-all text-[9px] uppercase font-bold tracking-widest"><X size={10} /> Clear Filters</button>
          </div>
        </div>

        {/* Listing Cards - The Heavy Part */}
        <div className="flex-1 overflow-y-auto p-3 scrollbar-hide">
          <AnimatePresence>
            {filteredListings.map((property) => (
              <ListingCard
                key={property.id}
                property={property}
                // isSelected prop removed as visual state is now on Mapbox
                onClick={() => setSelectedListing(property)}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Grip Handle */}
      <div style={{ width: HANDLE_WIDTH }} className="hidden md:flex h-full items-center justify-center cursor-pointer group bg-asta-deep/90 border-l border-white/5">
        <GripVertical size={16} className="text-white/20 group-hover:text-emerald-500 transition-colors" />
      </div>
    </motion.div>
  );
});

export default MapSidebar;
