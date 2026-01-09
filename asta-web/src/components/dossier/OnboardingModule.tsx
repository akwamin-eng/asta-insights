import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, ChevronRight, Fingerprint, Activity, Radio, MapPin, Check } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { SCOUT_CLASSES } from '../../lib/reputation';
import { getAvatarUrl } from '../../lib/avatar';

interface OnboardingProps {
  currentName: string;
  onComplete: () => void;
}

export default function OnboardingModule({ currentName, onComplete }: OnboardingProps) {
  const [step, setStep] = useState<'signal' | 'identity' | 'classification' | 'briefing'>('signal');
  const [codename, setCodename] = useState('');
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // AUTO-ADVANCE SIGNAL
  React.useEffect(() => {
    if (step === 'signal') {
      const timer = setTimeout(() => setStep('identity'), 3500);
      return () => clearTimeout(timer);
    }
  }, [step]);

  // HANDLERS
  const handleIdentityNext = () => {
    if (!codename.trim()) return;
    setStep('classification');
  };

  const handleFinalize = async () => {
    if (!selectedClass || !codename) return;
    setIsSaving(true);
    
    // Save generated avatar URL explicitly so it persists
    const generatedAvatar = getAvatarUrl(codename, 'bottts');

    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      await supabase.from('profiles').update({ 
        full_name: codename,
        scout_segment: selectedClass,
        rank_title: 'Observer',
        reputation_score: 10,
        avatar_url: generatedAvatar // Save the robot!
      }).eq('id', user.id);
    }

    setIsSaving(false);
    setStep('briefing');
  };

  return (
    <div className="absolute inset-0 z-[200] bg-black/95 backdrop-blur-xl flex flex-col items-center justify-center text-white font-sans p-6">
      <AnimatePresence mode="wait">
        
        {/* STAGE 1: SIGNAL */}
        {step === 'signal' && (
          <motion.div 
            key="signal"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="text-center space-y-6"
          >
            <div className="w-24 h-24 mx-auto rounded-full border border-emerald-500/30 flex items-center justify-center relative">
               <div className="absolute inset-0 border border-emerald-500 rounded-full animate-ping opacity-20" />
               <Radio size={48} className="text-emerald-500 animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold tracking-tighter uppercase text-emerald-500">Incoming Transmission</h2>
            <div className="font-mono text-xs text-emerald-500/70 space-y-1">
               <p>ENCRYPTION... <span className="text-emerald-400">VERIFIED</span></p>
               <p>SOURCE... <span className="text-emerald-400">CONNECTED</span></p>
            </div>
          </motion.div>
        )}

        {/* STAGE 2: IDENTITY (WITH AVATAR PREVIEW) */}
        {step === 'identity' && (
          <motion.div 
             key="identity"
             initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
             className="max-w-md w-full bg-[#111] border border-white/10 p-8 rounded-2xl shadow-2xl relative overflow-hidden"
          >
             <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500" />
             
             {/* DYNAMIC AVATAR PREVIEW */}
             <div className="flex justify-center mb-6">
               <div className="w-24 h-24 rounded-full border-2 border-emerald-500/50 bg-black overflow-hidden shadow-[0_0_20px_rgba(16,185,129,0.2)] transition-all">
                 <img 
                   src={getAvatarUrl(codename || 'unknown', 'bottts')} 
                   alt="Avatar Preview" 
                   className="w-full h-full object-cover"
                 />
               </div>
             </div>
             
             <h2 className="text-xl font-bold text-white text-center mb-2">Identify Yourself</h2>
             <p className="text-sm text-gray-400 text-center mb-6">
               Enter your codename to generate your digital signature.
             </p>

             <div className="space-y-4">
               <div className="relative">
                 <input 
                   type="text" 
                   value={codename}
                   onChange={(e) => setCodename(e.target.value)}
                   placeholder="e.g. Agent Wolf"
                   className="w-full bg-black border border-white/20 rounded-lg py-3 px-4 text-emerald-400 font-mono focus:outline-none focus:border-emerald-500 transition-colors uppercase tracking-widest text-center"
                   autoFocus
                 />
               </div>

               <button 
                 onClick={handleIdentityNext}
                 disabled={!codename}
                 className="w-full bg-white text-black hover:bg-gray-200 font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50"
               >
                 Next Step <ChevronRight size={16} />
               </button>
             </div>
          </motion.div>
        )}

        {/* STAGE 3: CLASSIFICATION */}
        {step === 'classification' && (
          <motion.div 
             key="classification"
             initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
             className="max-w-xl w-full bg-[#111] border border-white/10 p-8 rounded-2xl shadow-2xl relative overflow-hidden flex flex-col max-h-[80vh]"
          >
             <div className="absolute top-0 left-0 w-1/2 h-1 bg-emerald-500" />
             <div className="mb-6 text-center">
               <h2 className="text-xl font-bold text-white mb-2">Select Protocol</h2>
               <p className="text-sm text-gray-400">Assign your operating profile for the mission.</p>
             </div>

             <div className="grid gap-3 overflow-y-auto custom-scrollbar pr-2 mb-6">
                {SCOUT_CLASSES.map((c) => {
                  const Icon = c.icon;
                  const isSelected = selectedClass === c.id;
                  return (
                    <button
                      key={c.id}
                      onClick={() => setSelectedClass(c.id)}
                      className={`relative flex items-center gap-4 p-4 rounded-xl border text-left transition-all group ${
                        isSelected 
                          ? "bg-emerald-900/20 border-emerald-500 ring-1 ring-emerald-500/50" 
                          : "bg-white/5 border-white/10 hover:border-white/30 hover:bg-white/10"
                      }`}
                    >
                      <div className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-colors ${isSelected ? 'bg-emerald-500 text-black' : 'bg-black text-gray-400 group-hover:text-white'}`}>
                        <Icon size={18} />
                      </div>
                      <div className="flex-1">
                        <h3 className={`text-sm font-bold ${isSelected ? 'text-white' : 'text-gray-300'}`}>{c.label}</h3>
                        <p className={`text-[10px] leading-tight mt-0.5 ${isSelected ? 'text-emerald-200/70' : 'text-gray-500'}`}>{c.description}</p>
                      </div>
                      {isSelected && <div className="text-emerald-500"><Check size={18} /></div>}
                    </button>
                  );
                })}
             </div>

             <button 
               onClick={handleFinalize}
               disabled={!selectedClass || isSaving}
               className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 mt-auto shadow-lg"
             >
               {isSaving ? 'Establishing Uplink...' : <>Confirm Classification <ChevronRight size={16} /></>}
             </button>
          </motion.div>
        )}

        {/* STAGE 4: BRIEFING */}
        {step === 'briefing' && (
          <motion.div 
             key="briefing"
             initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
             className="max-w-4xl w-full text-center"
          >
             {/* Large Avatar Reveal */}
             <div className="w-32 h-32 mx-auto rounded-full border-4 border-emerald-500 shadow-[0_0_40px_rgba(16,185,129,0.4)] overflow-hidden mb-6 bg-black">
                 <img 
                   src={getAvatarUrl(codename, 'bottts')} 
                   alt="Final Avatar" 
                   className="w-full h-full object-cover"
                 />
             </div>
             
             <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Welcome, {codename}</h2>
             <p className="text-gray-400 mb-8">Your Unified Command Center is ready.</p>

             <button 
               onClick={onComplete}
               className="bg-white text-black font-bold px-10 py-4 rounded-full hover:bg-emerald-400 hover:scale-105 transition-all shadow-[0_0_30px_rgba(16,185,129,0.3)] text-sm uppercase tracking-widest"
             >
               Launch Command Center
             </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
