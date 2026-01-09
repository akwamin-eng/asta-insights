import React from 'react';
import { Shield, BadgeCheck, Globe, Briefcase, Lock, Zap } from 'lucide-react';
import type { UserProfile } from '../../types/asta_types';
import { getRankFromScore, getNextRank, SCOUT_CLASSES } from '../../lib/reputation';
import { getAvatarUrl } from '../../lib/avatar';

interface IdentityModuleProps {
  profile: UserProfile | null;
}

export default function IdentityModule({ profile }: IdentityModuleProps) {
  // GAME LOGIC
  const score = profile?.reputation_score || 0;
  const roleId = profile?.scout_segment || 'buyer';
  const codename = profile?.full_name || "Unknown Scout";
  
  const currentRank = getRankFromScore(score);
  const { next, progress, needed } = getNextRank(score);
  const userClass = SCOUT_CLASSES.find(c => c.id === roleId) || SCOUT_CLASSES[0];
  const ClassIcon = userClass.icon;

  // VISUALS
  const tierColors: Record<string, string> = {
    'IRON': 'border-gray-600 text-gray-400 bg-gray-500/10',
    'BRONZE': 'border-amber-700 text-amber-600 bg-amber-900/20',
    'SILVER': 'border-slate-300 text-slate-300 bg-slate-500/20',
    'GOLD': 'border-yellow-500 text-yellow-400 bg-yellow-500/20',
    'PLATINUM': 'border-cyan-400 text-cyan-400 bg-cyan-500/20 shadow-[0_0_15px_rgba(34,211,238,0.2)]',
  };

  const currentTierStyle = tierColors[currentRank.tier] || tierColors['IRON'];
  const isVerified = profile?.verification_tier === 'verified_scout' || profile?.verification_tier === 'pro_agent';

  // AVATAR LOGIC: Use uploaded photo OR generate one based on ID/Name
  const avatarSource = profile?.avatar_url || getAvatarUrl(profile?.id || codename, 'bottts');

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-6 h-full shadow-2xl relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none transition-transform group-hover:scale-110 duration-700">
        <Shield size={120} />
      </div>

      <div className="flex flex-col items-center text-center relative z-10">
        
        {/* AVATAR RING */}
        <div className="relative mb-4 group-hover:scale-105 transition-transform duration-300">
          <div className={`w-24 h-24 rounded-full border-2 overflow-hidden bg-black/50 flex items-center justify-center transition-all duration-500 ${currentTierStyle.split(' ')[0]}`}>
             <img 
               src={avatarSource} 
               alt="Profile" 
               className="w-full h-full object-cover"
             />
          </div>
          
          <div className={`absolute -bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border backdrop-blur-md whitespace-nowrap shadow-lg ${currentTierStyle}`}>
            {currentRank.title}
          </div>

          {isVerified && (
            <div className="absolute top-0 right-0 bg-black rounded-full p-1.5 border border-emerald-500 text-emerald-500 shadow-lg">
              <BadgeCheck size={14} fill="black" />
            </div>
          )}
        </div>

        {/* IDENTITY */}
        <h2 className="text-xl font-bold text-white mt-4 truncate w-full px-2 tracking-tight">
          {codename}
        </h2>
        
        <div className={`flex items-center gap-2 mt-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono uppercase ${userClass.color}`}>
           <ClassIcon size={12} />
           <span className="tracking-wider">{userClass.label}</span>
        </div>

        <p className="text-[9px] text-gray-600 font-mono mt-3 uppercase tracking-widest flex items-center gap-1 opacity-60">
          <Lock size={8} />
          ID: {profile?.id ? profile.id.slice(0, 12) : "AUTHENTICATING..."}
        </p>

        {/* STATS GRID */}
        <div className="grid grid-cols-2 gap-3 w-full mt-6">
           <div className={`bg-white/5 rounded-lg p-3 border border-white/5 flex flex-col items-center group hover:border-opacity-50 transition-colors ${currentTierStyle.split(' ')[0]}`}>
              <Shield size={16} className="mb-1 opacity-80" />
              <span className="text-2xl font-mono text-white font-bold">{score}</span>
              <span className="text-[9px] text-gray-500 uppercase font-bold tracking-tighter">Trust Score</span>
           </div>
           
           <div className="bg-white/5 rounded-lg p-3 border border-white/5 flex flex-col items-center group hover:border-emerald-500/30 transition-colors">
              <Zap size={16} className="text-emerald-500 mb-1" />
              <span className="text-2xl font-mono text-white font-bold">{next ? needed : 0}</span>
              <span className="text-[9px] text-gray-500 uppercase font-bold tracking-tighter">Pts to {next?.title || 'MAX'}</span>
           </div>
        </div>

        {/* PROGRESS */}
        <div className="w-full mt-6 space-y-2">
           <div className="flex justify-between text-[9px] text-gray-500 uppercase font-bold">
             <span>Level Progress</span>
             <span className={userClass.color.replace('text-', 'text-')}>{Math.round(progress)}%</span>
           </div>
           <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
             <div 
               className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-1000 relative" 
               style={{ width: `${progress}%` }}
             >
                <div className="absolute right-0 top-0 bottom-0 w-2 bg-white/50 blur-[2px]" />
             </div>
           </div>
        </div>

        {/* FOOTER */}
        <div className="mt-4 pt-4 border-t border-white/5 w-full">
           <div className="flex items-start gap-2 text-left opacity-60">
             <div className="mt-0.5 text-gray-400"><Briefcase size={10} /></div>
             <p className="text-[10px] text-gray-400 leading-tight">
               <strong className="text-gray-300 block mb-0.5">Current Clearance:</strong> 
               {currentRank.perk}
             </p>
           </div>
        </div>

      </div>
    </div>
  );
}
