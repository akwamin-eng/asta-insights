import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Mail, 
  ArrowRight, 
  Loader2, 
  CheckCircle, 
  ShieldCheck, 
  KeyRound, 
  Sparkles 
} from 'lucide-react';
import { supabase } from '../lib/supabase';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'magic' | 'password'>('magic'); // 👈 Mode Toggle

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    setError(null);

    try {
      if (mode === 'magic') {
        // ⚡ Magic Link Flow
        const { error } = await supabase.auth.signInWithOtp({
          email,
          options: { emailRedirectTo: window.location.origin },
        });
        if (error) throw error;
        setSent(true);
      } else {
        // 🔑 Password Flow (For Admins)
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        onClose(); // Success - close modal immediately
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
          />

          {/* Modal */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-md bg-[#0A0A0A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* Decorative Top Bar */}
            <div className="h-1 w-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-600" />

            <button 
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>

            <div className="p-8">
              {/* Header */}
              <div className="mb-6 text-center">
                <motion.div 
                  initial={false}
                  animate={{ rotate: mode === 'password' ? 360 : 0 }}
                  className="w-14 h-14 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/10 shadow-lg"
                >
                  {sent ? (
                    <CheckCircle className="text-emerald-500" />
                  ) : mode === 'magic' ? (
                    <ShieldCheck className="text-emerald-500" />
                  ) : (
                    <KeyRound className="text-emerald-500" />
                  )}
                </motion.div>
                
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  {sent ? 'Check your email' : 'Access the Terminal'}
                </h2>
                
                <p className="text-sm text-gray-400 mt-2">
                  {sent 
                    ? `We sent a magic link to ${email}`
                    : mode === 'magic' 
                      ? 'Sign in to access market intelligence.'
                      : 'Enter credentials to decrypt session.'}
                </p>
              </div>

              {/* Form */}
              {!sent ? (
                <form onSubmit={handleSubmit} className="space-y-4">
                  
                  {/* Email Field */}
                  <div className="space-y-1">
                    <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest ml-1">Email Identity</label>
                    <div className="relative group">
                      <Mail className="absolute left-3 top-3 text-gray-500 group-focus-within:text-emerald-500 transition-colors" size={18} />
                      <input 
                        type="email" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="name@example.com"
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500/50 focus:bg-white/10 transition-all text-sm"
                        autoFocus
                      />
                    </div>
                  </div>

                  {/* Password Field (Conditional Animation) */}
                  <AnimatePresence initial={false}>
                    {mode === 'password' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-1 overflow-hidden"
                      >
                        <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest ml-1">Access Key</label>
                        <div className="relative group">
                          <KeyRound className="absolute left-3 top-3 text-gray-500 group-focus-within:text-emerald-500 transition-colors" size={18} />
                          <input 
                            type="password" 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500/50 focus:bg-white/10 transition-all text-sm"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Error Message */}
                  {error && (
                    <motion.div 
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs text-center font-medium"
                    >
                      {error}
                    </motion.div>
                  )}

                  {/* Submit Button */}
                  <button 
                    disabled={loading}
                    className="w-full bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(255,255,255,0.2)]"
                  >
                    {loading ? (
                      <Loader2 className="animate-spin" size={18} />
                    ) : mode === 'magic' ? (
                      <>
                        Send Magic Link <ArrowRight size={18} />
                      </>
                    ) : (
                      <>
                        Authenticate <KeyRound size={18} />
                      </>
                    )}
                  </button>
                  
                  {/* Mode Toggle */}
                  <div className="pt-4 flex justify-center border-t border-white/5 mt-4">
                    <button 
                      type="button"
                      onClick={() => setMode(mode === 'magic' ? 'password' : 'magic')}
                      className="text-xs text-gray-500 hover:text-white transition-colors flex items-center gap-2 group"
                    >
                      {mode === 'magic' ? (
                        <>
                          <KeyRound size={12} className="group-hover:text-emerald-500 transition-colors" /> Switch to Password Login
                        </>
                      ) : (
                        <>
                          <Sparkles size={12} className="group-hover:text-emerald-500 transition-colors" /> Switch to Magic Link
                        </>
                      )}
                    </button>
                  </div>

                </form>
              ) : (
                <div className="text-center animate-in fade-in zoom-in duration-300">
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-6">
                    <p className="text-emerald-400 text-sm font-medium">Link dispatched successfully.</p>
                  </div>
                  <button 
                    onClick={onClose}
                    className="w-full bg-white/5 border border-white/10 text-white font-bold py-3 rounded-xl hover:bg-white/10 transition-all"
                  >
                    Close
                  </button>
                  <p 
                    className="text-xs text-gray-500 mt-4 cursor-pointer hover:text-emerald-500 transition-colors underline decoration-dotted" 
                    onClick={() => setSent(false)}
                  >
                    Use a different email address
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
