import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, X, ChevronRight, Loader2, Lock, ShieldCheck } from 'lucide-react';
import { supabase } from '../lib/supabase';

interface AuthOverlayProps {
  onClose: () => void;
}

export default function AuthOverlay({ onClose }: AuthOverlayProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: window.location.origin,
      },
    });

    setLoading(false);
    if (!error) {
      setSent(true);
    }
  };

  return (
    <div className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-md flex items-end md:items-center justify-center md:p-4">
      {/* CLICK OUTSIDE TO CLOSE */}
      <div className="absolute inset-0" onClick={onClose} />

      <motion.div 
        initial={{ y: "100%", opacity: 0, scale: 1 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: "100%", opacity: 0 }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="w-full max-w-sm bg-[#09090b] md:border border-white/10 md:rounded-2xl rounded-t-3xl overflow-hidden shadow-[0_-10px_40px_rgba(0,0,0,0.8)] relative z-10"
      >
        {/* TACTICAL ACCENT LINE */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500 to-transparent opacity-50" />
        
        {/* CLOSE BUTTON */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-gray-500 hover:text-white transition-colors z-20"
        >
          <X size={20} />
        </button>

        <div className="p-6 md:p-8 flex flex-col items-center text-center">
          
          {/* ICON GLOW */}
          <div className="relative mb-6">
            <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full" />
            <div className="relative w-14 h-14 bg-[#111] rounded-2xl border border-white/10 flex items-center justify-center text-emerald-400 shadow-xl">
              <Terminal size={24} />
            </div>
          </div>

          <h2 className="text-xl md:text-2xl font-bold text-white mb-2 tracking-tight">Access Terminal</h2>
          <p className="text-gray-400 text-xs md:text-sm mb-8 max-w-[260px] leading-relaxed">
            Authentication required to verify assets, save intel, and access the command network.
          </p>

          <AnimatePresence mode="wait">
            {sent ? (
              <motion.div 
                key="success"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-6 text-sm text-emerald-400 relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
                <ShieldCheck size={24} className="mx-auto mb-2 text-emerald-500" />
                <span className="font-bold block text-lg mb-1 text-white">Link Sent</span>
                <p className="opacity-80 text-xs">Secure entry key dispatched to:<br/><span className="font-mono text-emerald-300">{email}</span></p>
                <button onClick={onClose} className="mt-4 text-[10px] uppercase font-bold tracking-widest text-emerald-500 hover:text-white transition-colors">
                  Close Overlay
                </button>
              </motion.div>
            ) : (
              <motion.form 
                key="form"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onSubmit={handleLogin} 
                className="w-full space-y-4"
              >
                <div className="relative group">
                  <Lock size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-emerald-500 transition-colors" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter secure email..."
                    className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-10 pr-4 text-white text-base md:text-sm placeholder:text-gray-600 focus:border-emerald-500/50 focus:bg-white/10 focus:outline-none transition-all"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-white hover:bg-emerald-400 hover:text-black text-black font-bold py-4 rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50 text-xs md:text-sm uppercase tracking-widest shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <Loader2 size={16} className="animate-spin" /> ESTABLISHING UPLINK...
                    </span>
                  ) : (
                    <>Send Magic Link <ChevronRight size={14} /></>
                  )}
                </button>
              </motion.form>
            )}
          </AnimatePresence>

          <div className="mt-8 pt-6 border-t border-white/5 w-full">
            <p className="text-[10px] text-gray-600 font-mono uppercase tracking-wider">
              Encryption: AES-256 // Protocol: Supabase Auth
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
