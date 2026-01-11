import React, { useState, useEffect } from 'react';
import { Calculator, Hammer, Truck, ArrowRight, Info } from 'lucide-react';

export default function DevelopmentCostCalculator({ acres, topography }: { acres: number, topography: string }) {
  const [wallCost, setWallCost] = useState(0);
  const [fillCost, setFillCost] = useState(0);
  
  // Constants for Ghana Construction (approximate GHS)
  const COST_PER_BLOCK_LAYED = 18; // Block + Mortar + Labor
  const BLOCKS_PER_ACRE_PERIMETER = 1100; // Rough estimate for standard 7ft wall
  const FILL_TRUCK_COST = 800; // Per trip (20 cubic yards)

  useEffect(() => {
    calculate();
  }, [acres, topography]);

  const calculate = () => {
    // 1. Walling Cost
    // Perimeter scales with sqrt of area. 1 Acre square ~835ft perimeter.
    // 1 acre = 4046 sqm. Sqrt(4046) = 63.6m side. 63.6*4 = 254m perimeter.
    // 254m / 0.4m (block length) = 635 blocks per course.
    // 8 courses high (2m wall) = 5080 blocks. 
    // Let's simplify: Standard 70x100 plot (0.16 acre) takes ~1800 blocks.
    // Scaling factor:
    const plots = acres / 0.16;
    const baseBlocks = 1800 * Math.sqrt(plots); // Perimeter logic
    const totalWalling = baseBlocks * COST_PER_BLOCK_LAYED;

    // 2. Land Fill / Grading
    let trucksNeeded = 0;
    if (topography === 'waterlogged') trucksNeeded = plots * 20; // Heavy fill
    if (topography === 'sloped') trucksNeeded = plots * 5; // Grading
    if (topography === 'rocky') trucksNeeded = plots * 8; // Breaking/Clearing
    
    const totalFill = trucksNeeded * FILL_TRUCK_COST;

    setWallCost(Math.round(totalWalling));
    setFillCost(Math.round(totalFill));
  };

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-5 hover:border-emerald-500/30 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white font-bold text-sm flex items-center gap-2">
            <Calculator size={16} className="text-emerald-500" />
            Development Estimator
          </h3>
          <p className="text-[10px] text-gray-500">Estimated cost to secure & prep land</p>
        </div>
        <div className="bg-emerald-500/10 px-2 py-1 rounded text-[10px] text-emerald-400 font-bold border border-emerald-500/20">
          GHS Estimate
        </div>
      </div>

      <div className="space-y-4">
        {/* Wall Cost */}
        <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-500">
              <Hammer size={14} />
            </div>
            <div>
              <p className="text-xs text-gray-300 font-bold">Perimeter Wall</p>
              <p className="text-[10px] text-gray-500">Sandcrete blocks & labor</p>
            </div>
          </div>
          <span className="text-sm font-mono font-bold text-white">₵{wallCost.toLocaleString()}</span>
        </div>

        {/* Fill Cost */}
        <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500">
              <Truck size={14} />
            </div>
            <div>
              <p className="text-xs text-gray-300 font-bold">Land Prep / Fill</p>
              <p className="text-[10px] text-gray-500 capitalize">{topography} Terrain</p>
            </div>
          </div>
          <span className="text-sm font-mono font-bold text-white">₵{fillCost.toLocaleString()}</span>
        </div>

        <div className="pt-2 border-t border-white/10 flex justify-between items-center">
          <p className="text-[10px] text-gray-500 flex items-center gap-1">
            <Info size={10} /> Based on 2026 market rates
          </p>
          <div className="text-right">
            <p className="text-[10px] text-gray-400 uppercase font-bold">Total Prep Cost</p>
            <p className="text-lg font-bold text-emerald-400 font-mono">₵{(wallCost + fillCost).toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
