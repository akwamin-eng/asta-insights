import React, { useState, useEffect, useRef } from "react";
import {
  Target,
  DollarSign,
  X,
  Loader2,
  CheckCircle2,
  Search,
  Crosshair,
  Navigation,
  RefreshCw,
  Info,
  Building,
  Home,
  Briefcase,
  GraduationCap,
  PartyPopper,
} from "lucide-react";
import { useGoogleAutocomplete } from "../../hooks/useGoogleAutocomplete";
import { motion, AnimatePresence } from "framer-motion";
// NEW IMPORTS FOR DATABASE WRITE
import { supabase } from "../../lib/supabase";
import { useAuth } from "../../hooks/useAuth";
// NEW IMPORT FOR URL PARAMS
import { useSearchParams } from "react-router-dom";

interface HunterPreferencesProps {
  preferences: any;
  onUpdate: (updates: any) => void;
}

// --- INTERNAL COMPONENT: SECTION TOOLTIP ---
const SectionTooltip = ({ title, text }: { title: string; text: string }) => (
  <div className="group relative inline-block ml-2 pointer-events-auto z-50">
    <Info
      size={12}
      className="text-gray-600 hover:text-emerald-500 cursor-help transition-colors"
    />
    <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-56 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none z-50">
      <div className="bg-black/95 backdrop-blur-xl border border-white/10 text-white text-[10px] p-3 rounded-lg shadow-xl">
        <h4 className="font-bold text-emerald-400 uppercase tracking-wider mb-1">
          {title}
        </h4>
        <p className="text-gray-400 leading-relaxed">{text}</p>
        <div className="w-2 h-2 bg-black border-r border-b border-white/10 rotate-45 absolute left-1/2 -translate-x-1/2 -bottom-1"></div>
      </div>
    </div>
  </div>
);

export default function HunterPreferences({
  preferences,
  onUpdate,
}: HunterPreferencesProps) {
  const {
    predictions,
    getPredictions,
    loading: searching,
    setPredictions,
  } = useGoogleAutocomplete();
  const { user } = useAuth(); // GET USER TO WRITE TO DB
  const [searchParams] = useSearchParams(); // READ URL PARAMS

  const [inputZone, setInputZone] = useState("");

  // CURRENCY STATE
  const [currency, setCurrency] = useState<"GHS" | "USD">("GHS");
  const EX_RATE = 12.5;

  // --- STATE MANAGEMENT ---
  const [budget, setBudget] = useState(preferences?.budget_max || 250000);
  const [localLocations, setLocalLocations] = useState<string[]>(
    preferences?.locations || []
  );

  // NEW: Asset Class & Lifestyle
  const [assetTypes, setAssetTypes] = useState<string[]>(
    preferences?.property_type || []
  );
  const [lifestyleTags, setLifestyleTags] = useState<string[]>(
    preferences?.lifestyle_tags || []
  );

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Sync props to state (Initial Load Only + URL Param Check)
  useEffect(() => {
    // 1. Load DB Preferences into State
    if (preferences) {
      if (preferences.budget_max) setBudget(preferences.budget_max);
      // We handle locations below to merge with URL param
      if (preferences.property_type && assetTypes.length === 0)
        setAssetTypes(preferences.property_type);
      if (preferences.lifestyle_tags && lifestyleTags.length === 0)
        setLifestyleTags(preferences.lifestyle_tags);
    }

    // 2. Handle URL Parameter Injection (Auto-fill from Map Search)
    const urlZone = searchParams.get("zone");
    const existingLocations = preferences?.locations || [];

    if (urlZone) {
      // If we have a URL zone, add it to existing locations if not already present
      const combinedLocations = existingLocations.includes(urlZone)
        ? existingLocations
        : [...existingLocations, urlZone];

      // Update state with the combined list
      // We use JSON.stringify for a quick array comparison to prevent infinite loops
      if (
        JSON.stringify(combinedLocations) !== JSON.stringify(localLocations)
      ) {
        setLocalLocations(combinedLocations);
      }
    } else {
      // Standard sync if no URL param: just use DB preferences
      if (preferences?.locations && localLocations.length === 0) {
        setLocalLocations(preferences.locations);
      }
    }
  }, [preferences, searchParams]);

  // Click Outside Logic
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setPredictions([]);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setPredictions]);

  // --- HANDLERS ---

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputZone(val);
    getPredictions(val);
  };

  const selectZone = (description: string) => {
    const cleanName = description.split(",")[0].trim();
    if (!localLocations.includes(cleanName)) {
      const newZones = [...localLocations, cleanName];
      setLocalLocations(newZones);
    }
    setInputZone("");
    setPredictions([]);
  };

  const removeZone = (e: React.MouseEvent, zone: string) => {
    e.stopPropagation();
    const newZones = localLocations.filter((z: string) => z !== zone);
    setLocalLocations(newZones);
  };

  const toggleAssetType = (type: string) => {
    setAssetTypes((prev) => {
      const next = prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type];
      return next;
    });
  };

  const toggleLifestyle = (tag: string) => {
    setLifestyleTags((prev) => {
      const next = prev.includes(tag)
        ? prev.filter((t) => t !== tag)
        : [...prev, tag];
      return next;
    });
  };

  const handleSaveProtocol = async () => {
    setIsSaving(true);

    // 1. Construct the payload
    const updates = {
      locations: localLocations,
      budget_max: budget,
      property_type: assetTypes,
      lifestyle_tags: lifestyleTags,
    };

    // 2. Write to DB (This enables the Map to see the changes)
    if (user) {
      await supabase
        .from("profiles")
        .update({ preferences: updates })
        .eq("id", user.id);
    }

    // 3. Update Local State (via parent)
    onUpdate(updates);

    // 4. UX Feedback
    await new Promise((r) => setTimeout(r, 600));
    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const displayBudget = currency === "GHS" ? budget : budget / EX_RATE;
  const filteredPredictions = predictions.filter((p: any) =>
    p.description.toLowerCase().includes("ghana")
  );

  return (
    <div className="bg-black/60 border border-emerald-500/20 rounded-xl p-6 h-full flex flex-col relative overflow-visible shadow-[0_0_50px_rgba(16,185,129,0.05)] overflow-y-auto custom-scrollbar">
      {/* Tactical Header */}
      <div className="mb-6 shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <div className="p-1.5 bg-emerald-500/10 rounded border border-emerald-500/30">
            <Target className="text-emerald-500" size={18} />
          </div>
          <h2 className="text-sm font-black text-white uppercase tracking-[0.2em] flex items-center">
            Hunter Directives
          </h2>
        </div>
        <p className="text-[10px] text-emerald-500/60 font-mono uppercase tracking-wider">
          Sector Surveillance & Capital Thresholds
        </p>
      </div>

      <div className="space-y-8 flex-1">
        {/* 1. ZONE DISCOVERY */}
        <div className="space-y-4 relative" ref={dropdownRef}>
          <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            <Navigation size={10} /> Authorized Sectors
          </label>

          <div className="relative group">
            <div
              className={`flex items-center bg-black border ${
                searching ? "border-emerald-500/50" : "border-white/10"
              } rounded-lg px-3 py-1 transition-all`}
            >
              <Search size={14} className="text-gray-500" />
              <input
                type="text"
                value={inputZone}
                onChange={handleInputChange}
                placeholder="Search zones (e.g. East Legon)..."
                className="flex-1 bg-transparent border-none py-2 px-3 text-xs text-white focus:outline-none font-mono"
              />
              {searching && (
                <Loader2 size={14} className="text-emerald-500 animate-spin" />
              )}
            </div>

            <AnimatePresence>
              {inputZone.length > 2 && filteredPredictions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full left-0 right-0 mt-2 bg-[#0A0A0A] border border-emerald-500/30 rounded-lg shadow-2xl z-[200] overflow-hidden"
                >
                  {filteredPredictions.map((p: any) => (
                    <button
                      key={p.place_id}
                      onClick={() => selectZone(p.description)}
                      className="w-full text-left px-4 py-3 hover:bg-emerald-500/10 border-b border-white/5 last:border-0 transition-colors group"
                    >
                      <div className="text-[11px] text-white font-bold group-hover:text-emerald-400 transition-colors">
                        {p.structured_formatting.main_text}
                      </div>
                      <div className="text-[9px] text-gray-500 font-mono">
                        {p.structured_formatting.secondary_text}
                      </div>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="flex flex-wrap gap-2 min-h-[32px]">
            {localLocations.map((zone: string) => (
              <motion.span
                layout
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                key={zone}
                className="group flex items-center gap-2 px-3 py-1.5 rounded bg-emerald-500/5 border border-emerald-500/20 text-emerald-500 text-[10px] font-black uppercase tracking-tight"
              >
                <Crosshair size={10} className="text-emerald-500/50" />
                {zone}
                <button
                  onClick={(e) => removeZone(e, zone)}
                  className="text-gray-600 hover:text-red-500 transition-colors"
                >
                  <X size={12} />
                </button>
              </motion.span>
            ))}
          </div>
        </div>

        {/* 2. ASSET CLASS */}
        <div className="space-y-4">
          <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            <Building size={10} /> Asset Class
            <SectionTooltip
              title="Asset Classification"
              text="Filter by property structure. 'Apt' includes condos/flats. 'House' includes townhomes and detached units."
            />
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "apartment", label: "Apt", icon: Building },
              { id: "house", label: "House", icon: Home },
              { id: "commercial", label: "Comm.", icon: Briefcase },
            ].map((type) => {
              const isActive = assetTypes.includes(type.id);
              const Icon = type.icon;
              return (
                <button
                  key={type.id}
                  onClick={() => toggleAssetType(type.id)}
                  className={`flex flex-col items-center justify-center gap-1.5 py-3 rounded-lg border transition-all ${
                    isActive
                      ? "bg-emerald-500/20 border-emerald-500 text-white"
                      : "bg-black border-white/10 text-gray-500 hover:bg-white/5"
                  }`}
                >
                  <Icon
                    size={14}
                    className={isActive ? "text-emerald-400" : "text-gray-600"}
                  />
                  <span className="text-[9px] font-bold uppercase">
                    {type.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. OPERATIONAL CONTEXT (LIFESTYLE) */}
        <div className="space-y-4">
          <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            <Target size={10} /> Operational Context
            <SectionTooltip
              title="Operational Context"
              text="Lifestyle-driven filters. 'Near HQ' prioritizes commute routes. 'School Run' targets proximity to major international schools."
            />
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "near_hq", label: "Near HQ", icon: Briefcase },
              { id: "school_run", label: "School Run", icon: GraduationCap },
              { id: "night_ops", label: "Night Ops", icon: PartyPopper },
            ].map((tag) => {
              const isActive = lifestyleTags.includes(tag.id);
              const Icon = tag.icon;
              return (
                <button
                  key={tag.id}
                  onClick={() => toggleLifestyle(tag.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded border transition-all ${
                    isActive
                      ? "bg-blue-500/20 border-blue-500 text-white"
                      : "bg-black border-white/10 text-gray-500 hover:bg-white/5"
                  }`}
                >
                  <Icon
                    size={12}
                    className={isActive ? "text-blue-400" : "text-gray-600"}
                  />
                  <span className="text-[9px] font-bold uppercase truncate">
                    {tag.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 4. BUDGET LOGIC */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
              <DollarSign size={10} /> Valuation Cap
            </label>
            <div className="flex bg-black border border-white/10 rounded p-0.5">
              {["GHS", "USD"].map((curr) => (
                <button
                  key={curr}
                  onClick={() => setCurrency(curr as any)}
                  className={`px-2 py-0.5 text-[8px] font-bold rounded transition-all ${
                    currency === curr
                      ? "bg-emerald-600 text-white"
                      : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {curr}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-black border border-white/10 rounded-lg p-4">
            <div className="flex justify-between items-end mb-4">
              <span className="text-2xl font-black text-white font-mono">
                {currency === "GHS" ? "₵" : "$"}
                {displayBudget > 1000
                  ? `${(displayBudget / 1000).toFixed(1)}k`
                  : displayBudget.toFixed(0)}
              </span>
              <span className="text-[10px] text-gray-500 font-mono uppercase">
                {currency} Limit
              </span>
            </div>
            <input
              type="range"
              min={currency === "GHS" ? "50000" : (50000 / EX_RATE).toString()}
              max={
                currency === "GHS" ? "5000000" : (5000000 / EX_RATE).toString()
              }
              step={currency === "GHS" ? "10000" : "1000"}
              value={displayBudget}
              onChange={(e) => {
                const val = Number(e.target.value);
                setBudget(currency === "GHS" ? val : val * EX_RATE);
              }}
              className="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>
        </div>
      </div>

      {/* SAVE BUTTON */}
      <button
        onClick={handleSaveProtocol}
        disabled={isSaving || saveSuccess}
        className={`mt-6 w-full py-4 font-black text-[10px] uppercase tracking-[0.2em] rounded-lg transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] flex items-center justify-center gap-2 shrink-0 ${
          saveSuccess
            ? "bg-white text-emerald-600 border border-emerald-500"
            : "bg-emerald-600 hover:bg-emerald-500 text-white"
        }`}
      >
        {isSaving ? (
          <>
            <RefreshCw size={14} className="animate-spin" /> UPDATING
            PROTOCOL...
          </>
        ) : saveSuccess ? (
          <>
            <CheckCircle2 size={14} /> PROTOCOL ACTIVE
          </>
        ) : (
          <>
            <CheckCircle2 size={14} /> UPDATE HUNT PROTOCOL
          </>
        )}
      </button>

      {/* STATUS LINE */}
      <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center opacity-30 font-mono text-[8px] shrink-0">
        <span>STATUS: ACTIVE</span>
        <span>SCAN_MODE: GLOBAL_GH</span>
      </div>
    </div>
  );
}
