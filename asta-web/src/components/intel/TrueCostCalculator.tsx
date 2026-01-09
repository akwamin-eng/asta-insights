import React, { useState } from 'react';
import { Calculator, Zap, Droplets, Shield, ChevronDown, ChevronUp, Info, Lock, ShieldAlert } from 'lucide-react';
import { useProfile } from '../../hooks/useProfile';

interface TrueCostProps {
  price: number;
  currency: 'GHS' | 'USD';
  bedrooms: number;
  type: 'sale' | 'rent';
}

export default function TrueCostCalculator({ price, currency, bedrooms, type }: TrueCostProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { profile } = useProfile();

  // --- GAMIFICATION LOCK LOGIC ---
  const REQUIRED_SCORE = 200; // Silver Tier
  const currentScore = profile?.reputation_score || 0;
  const isLocked = currentScore < REQUIRED_SCORE;
  const progress = Math.min(100, (currentScore / REQUIRED_SCORE) * 100);

  // LOGIC: Ghana Market Estimates (Monthly)
  const SERVICE_CHARGE_PCT = 0.12; // 12% is standard for managed compounds
  const ECG_PER_BED = 400; // ~400 GHS electricity per bedroom
  const WATER_FLAT = 150;  // Flat rate for GWCL
  const GEN_FUEL_EST = 600; // Estimated diesel cost for standby gen

  // Calculations
  const basePrice = price;
  const serviceCharge = Math.round(basePrice * SERVICE_CHARGE_PCT);
  
  // Utility Logic (Only applicable if Renting usually, or living in own home)
  // We assume currency conversion if USD listing but costs are in GHS
  const rate = currency === 'USD' ? 15.5 : 1; 
  
  // Utilities are always calculated in local currency first, then converted to display currency
  const utilCostGHS = (ECG_PER_BED * (bedrooms || 1)) + WATER_FLAT + GEN_FUEL_EST;
  const utilCost = Math.round(utilCostGHS / rate);

  const totalCost = basePrice + serviceCharge + utilCost;
  const hiddenCostPct = Math.round(((totalCost - basePrice) / basePrice) * 100);

  if (type === 'sale') return null; // Currently optimized for Renters

  return (
    <div className="mt-4 bg-[#151515] border border-white/5 rounded-xl overflow-hidden transition-all relative">
      
      {/* HEADER */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg border ${isLocked ? 'bg-gray-800 border-gray-700 text-gray-500' : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'}`}>
            {isLocked ? <Lock size={18} /> : <Calculator size={18} />}
          </div>
          <div className="text-left">
            <h3 className={`text-xs font-bold uppercase tracking-wider ${isLocked ? 'text-gray-500' : 'text-white'}`}>
              {isLocked ? 'Restricted Intelligence' : 'True Cost of Living'}
            </h3>
            <p className="text-[10px] text-gray-500">
              {isLocked ? 'Clearance Level: SILVER' : 'Includes utilities & fees'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
           {/* If Open or Locked, hide the quick summary to force engagement */}
           {!isOpen && !isLocked && (
             <div className="text-right">
                <span className="text-sm font-mono text-indigo-400 font-bold">
                  {currency === 'GHS' ? '₵' : '$'}{totalCost.toLocaleString()}
                </span>
                <span className="text-[9px] text-red-400 block">+{hiddenCostPct}% Hidden</span>
             </div>
           )}
           {isOpen ? <ChevronUp size={16} className="text-gray-500"/> : <ChevronDown size={16} className="text-gray-500"/>}
        </div>
      </button>

      {/* EXPANDED CONTENT */}
      {isOpen && (
        <div className="p-4 pt-0 border-t border-white/5 bg-black/20 relative">
          
          {/* --- LOCKED OVERLAY --- */}
          {isLocked && (
            <div className="absolute inset-0 z-20 bg-[#151515]/90 backdrop-blur-[2px] flex flex-col items-center justify-center p-6 text-center select-none">
              <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-3 border border-white/10">
                 <ShieldAlert size={24} className="text-gray-500" />
              </div>
              <h4 className="text-white font-bold text-xs uppercase tracking-widest mb-1">Clearance Denied</h4>
              <p className="text-gray-400 text-[10px] mb-4 max-w-[220px] leading-relaxed">
                Detailed financial breakdowns, including hidden fees and utility estimates, are reserved for <strong className="text-gray-300">Operative</strong> rank and above.
              </p>
              
              {/* Progress Bar */}
              <div className="w-full max-w-[200px] space-y-1.5">
                <div className="flex justify-between text-[9px] font-mono text-gray-500 uppercase font-bold">
                  <span>Current: {currentScore} XP</span>
                  <span>Target: {REQUIRED_SCORE} XP</span>
                </div>
                <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-1000 ease-out" 
                    style={{ width: `${progress}%` }} 
                  />
                </div>
                <p className="text-[9px] text-emerald-500 font-bold mt-2 animate-pulse">
                  Mission: Verify {Math.ceil((REQUIRED_SCORE - currentScore) / 15)} more assets to unlock.
                </p>
              </div>
            </div>
          )}

          {/* --- DATA (Blurred if Locked) --- */}
          <div className={`space-y-3 mt-4 transition-all duration-500 ${isLocked ? 'blur-sm opacity-20 pointer-events-none' : ''}`}>
            
            {/* Base Rent */}
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Base Rent</span>
              <span className="font-mono text-white opacity-60">
                {currency === 'GHS' ? '₵' : '$'}{basePrice.toLocaleString()}
              </span>
            </div>

            {/* Service Charge */}
            <div className="flex justify-between items-center text-xs">
              <div className="flex items-center gap-2 text-gray-300">
                <Shield size={12} className="text-emerald-500" />
                <span>Service Charge (Est. 12%)</span>
              </div>
              <span className="font-mono text-white">
                +{currency === 'GHS' ? '₵' : '$'}{serviceCharge.toLocaleString()}
              </span>
            </div>

            {/* Utilities */}
            <div className="flex justify-between items-center text-xs">
              <div className="flex items-center gap-2 text-gray-300">
                <Zap size={12} className="text-yellow-500" />
                <span>ECG & Water (Est.)</span>
              </div>
              <span className="font-mono text-white">
                +{currency === 'GHS' ? '₵' : '$'}{Math.round(((ECG_PER_BED * (bedrooms || 1)) + WATER_FLAT) / rate).toLocaleString()}
              </span>
            </div>

            {/* Generator */}
            <div className="flex justify-between items-center text-xs">
              <div className="flex items-center gap-2 text-gray-300">
                <Droplets size={12} className="text-orange-500" />
                <span>Generator Fuel (Est.)</span>
              </div>
              <span className="font-mono text-white">
                +{currency === 'GHS' ? '₵' : '$'}{Math.round(GEN_FUEL_EST / rate).toLocaleString()}
              </span>
            </div>

            {/* Total Line */}
            <div className="pt-3 border-t border-white/10 flex justify-between items-end">
              <div className="flex items-center gap-1.5 text-[9px] text-gray-500">
                <Info size={10} /> 
                <span>Estimates based on local averages.</span>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-gray-400 uppercase">Real Monthly Cost</div>
                <div className="text-xl font-black font-mono text-indigo-400">
                   {currency === 'GHS' ? '₵' : '$'}{totalCost.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
