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

    setStatus('analyzing');
    await new Promise(r => setTimeout(r, 1200));
    setStatus('submitting');

    let category = 'logic';
    if (report.toLowerCase().includes('map')) category = 'map';
    if (report.toLowerCase().includes('login')) category = 'auth';
    if (report.toLowerCase().includes('look')) category = 'ui';

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
    }
  };

  return (
    <div className="fixed inset-0 z-[300] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 pointer-events-auto">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-sm bg-[#0A0A0A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
      >
        <div className="p-4 border-b border-white/5 flex justify-between items-center bg-red-500/5">
          <div className="flex items-center gap-2">
            <Bug size={16} className="text-red-500" />
            <span className="text-xs font-bold text-white uppercase tracking-widest">Bug Hunter v1.0</span>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors"><X size={16} /></button>
        </div>

        <div className="p-4 min-h-[200px] flex flex-col">
          <AnimatePresence mode="wait">
            {status === 'idle' && (
              <motion.form key="idle" onSubmit={handleSubmit} className="space-y-4">
                <p className="text-[10px] text-gray-500 leading-relaxed font-mono uppercase">// describe the system anomaly:</p>
                <textarea 
                  required value={report} onChange={(e) => setReport(e.target.value)}
                  placeholder="e.g. Map pins aren't loading..."
                  className="w-full bg-black border border-white/10 rounded-xl p-3 text-sm text-white focus:border-red-500/50 focus:outline-none min-h-[100px] resize-none font-mono"
                />
                <button type="submit" className="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-[10px] uppercase tracking-widest">
                  <Send size={14} /> Transmit Error Log
                </button>
              </motion.form>
            )}
            {/* ... other status states as before ... */}
            {status === 'analyzing' && <div className="flex-1 flex flex-col items-center justify-center text-center"><Loader2 className="animate-spin text-red-500" /></div>}
            {status === 'done' && <div className="flex-1 flex flex-col items-center justify-center text-center text-emerald-500"><CheckCircle size={40} /></div>}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
