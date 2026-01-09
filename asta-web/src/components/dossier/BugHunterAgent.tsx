import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bug, X, Send, Loader2, CheckCircle, Terminal } from 'lucide-react';
import { supabase } from '../../lib/supabase';

interface BugHunterProps {
  onClose: () => void;
}

export default function BugHunterAgent({ onClose }: BugHunterProps) {
  const [report, setReport] = useState('');
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'submitting' | 'done'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!report.trim()) return;

    // Phase 1: Simulation
    setStatus('analyzing');
    await new Promise(r => setTimeout(r, 1200));
    
    // Phase 2: Submission
    setStatus('submitting');

    let category = 'logic';
    const lower = report.toLowerCase();
    if (lower.includes('map')) category = 'map';
    if (lower.includes('login') || lower.includes('auth')) category = 'auth';
    if (lower.includes('css') || lower.includes('ui') || lower.includes('look')) category = 'ui';

    const { error } = await supabase.from('bug_reports').insert({
      description: report,
      category,
      metadata: { url: window.location.href, userAgent: navigator.userAgent }
    });

    if (!error) {
      setStatus('done');
      setTimeout(() => {
        onClose();
      }, 2000);
    } else {
      // Fallback if error
      setStatus('idle');
      alert("Transmission failed. Please try again.");
    }
  };

  return (
    <div className="fixed inset-0 z-[300] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 pointer-events-auto">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }} 
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="w-full max-w-sm bg-[#0A0A0A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
      >
        <div className="p-4 border-b border-white/5 flex justify-between items-center bg-red-500/5">
          <div className="flex items-center gap-2">
            <Bug size={16} className="text-red-500" />
            <span className="text-xs font-bold text-white uppercase tracking-widest">Bug Hunter v1.0</span>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="p-4 min-h-[220px] flex flex-col relative">
          <AnimatePresence mode="wait">
            {status === 'idle' && (
              <motion.form 
                key="idle" 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                onSubmit={handleSubmit} 
                className="space-y-4 flex-1 flex flex-col"
              >
                <div className="flex items-center gap-2 text-[10px] text-gray-500 font-mono uppercase">
                  <Terminal size={10} />
                  <span>// Describe system anomaly:</span>
                </div>
                <textarea 
                  required 
                  autoFocus
                  value={report} 
                  onChange={(e) => setReport(e.target.value)}
                  placeholder="e.g. Map pins aren't loading..."
                  className="w-full flex-1 bg-black border border-white/10 rounded-xl p-3 text-sm text-white focus:border-red-500/50 focus:outline-none resize-none font-mono placeholder-gray-700"
                />
                <button type="submit" className="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-[10px] uppercase tracking-widest transition-colors shadow-lg shadow-red-900/20">
                  <Send size={14} /> Transmit Error Log
                </button>
              </motion.form>
            )}

            {status === 'analyzing' && (
              <motion.div 
                key="analyzing"
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                className="flex-1 flex flex-col items-center justify-center text-center space-y-4"
              >
                <Loader2 className="w-10 h-10 text-red-500 animate-spin" />
                <div className="space-y-1">
                  <h3 className="text-white font-bold text-sm">Analyzing Report</h3>
                  <p className="text-xs text-gray-500 font-mono">Categorizing vector...</p>
                </div>
              </motion.div>
            )}

            {status === 'submitting' && (
              <motion.div 
                key="submitting"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-center space-y-4"
              >
                <Loader2 className="w-10 h-10 text-red-500/50 animate-spin" />
                <div className="space-y-1">
                  <h3 className="text-white font-bold text-sm">Transmitting</h3>
                  <p className="text-xs text-gray-500 font-mono">Establishing secure link...</p>
                </div>
              </motion.div>
            )}

            {status === 'done' && (
              <motion.div 
                key="done"
                initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
                className="flex-1 flex flex-col items-center justify-center text-center space-y-4"
              >
                <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-500">
                  <CheckCircle size={24} />
                </div>
                <div className="space-y-1">
                  <h3 className="text-white font-bold text-sm">Log Received</h3>
                  <p className="text-xs text-gray-500 font-mono">Command has been notified.</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
