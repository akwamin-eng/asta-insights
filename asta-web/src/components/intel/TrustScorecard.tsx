import React, { useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Info, MapPin, UserCheck, Users } from 'lucide-react';
import { calculateTrustScore } from '../../lib/intelligence';
import { motion, AnimatePresence } from 'framer-motion';

interface TrustScorecardProps {
  property: any;
  owner?: any; // The profile object of the lister
}

export default function TrustScorecard({ property, owner }: TrustScorecardProps) {
  const [expanded, setExpanded] = useState(false);
  const { score, grade, label, color, breakdown } = calculateTrustScore(property, owner);

  // Icon Selection based on grade
  const Icon = grade === 'A' ? ShieldCheck : grade === 'F' ? ShieldAlert : Shield;
  
  // Background Glow based on grade
  const glowColor = grade === 'A' ? 'shadow-[0_0_20px_rgba(52,211,153,0.3)]' : 
                    grade === 'F' ? 'shadow-[0_0_20px_rgba(220,38,38,0.3)]' : 'shadow-none';

  return (
    <div className={`rounded-xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden transition-all duration-300 ${glowColor}`}>
      
      {/* HEADER - Always Visible */}
      <div 
        onClick={() => setExpanded(!expanded)}
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white/5 border border-white/10 ${color}`}>
            <Icon size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Diaspora Trust Score</h3>
              <span className={`text-xs font-mono px-1.5 py-0.5 rounded border border-white/10 ${color} bg-white/5`}>
                GRADE {grade}
              </span>
            </div>
            <p className={`text-[10px] font-mono mt-1 ${color}`}>{label}</p>
          </div>
        </div>
        
        <div className="text-right">
          <span className="text-2xl font-black text-white font-mono">{score}</span>
          <span className="text-[9px] text-gray-500 block uppercase">/ 100 PTS</span>
        </div>
      </div>

      {/* EXPANDED DETAILS */}
      <AnimatePresence>
        {expanded && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/10 bg-black/20"
          >
            <div className="p-4 space-y-3">
              <p className="text-[10px] text-gray-400 mb-4 leading-relaxed">
                This automated score assesses risk factors for remote buyers. 
                It is not a guarantee of title, but a measure of data fidelity.
              </p>

              {/* FACTOR 1: AGENT */}
              <div className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2 text-gray-300">
                  <UserCheck size={12} className="text-emerald-500" />
                  <span>Agent Verification</span>
                </div>
                <div className="font-mono text-white">
                  {breakdown.agentTrust}/40
                </div>
              </div>
              <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500" style={{ width: `${(breakdown.agentTrust / 40) * 100}%` }} />
              </div>

              {/* FACTOR 2: LOCATION */}
              <div className="flex justify-between items-center text-xs mt-2">
                <div className="flex items-center gap-2 text-gray-300">
                  <MapPin size={12} className="text-blue-500" />
                  <span>Geo-Accuracy</span>
                </div>
                <div className="font-mono text-white">
                  {breakdown.locationFidelity}/25
                </div>
              </div>
              <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500" style={{ width: `${(breakdown.locationFidelity / 25) * 100}%` }} />
              </div>

              {/* FACTOR 3: SOCIAL */}
              <div className="flex justify-between items-center text-xs mt-2">
                <div className="flex items-center gap-2 text-gray-300">
                  <Users size={12} className="text-purple-500" />
                  <span>Scout Consensus</span>
                </div>
                <div className="font-mono text-white">
                  {breakdown.socialProof}/20
                </div>
              </div>
              <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500" style={{ width: `${(breakdown.socialProof / 20) * 100}%` }} />
              </div>

              <div className="mt-4 pt-3 border-t border-white/10 flex items-start gap-2">
                <Info size={12} className="text-gray-500 mt-0.5" />
                <p className="text-[9px] text-gray-600">
                  To improve this score, request a Field Scout Verification (+30 pts) or upload Land Title Documents (+15 pts).
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
