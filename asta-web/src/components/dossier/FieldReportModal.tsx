import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, X, Camera, MapPin, AlertTriangle, CheckCircle, Star } from 'lucide-react';
import { useFieldReport } from '../../hooks/useFieldReport';

interface FieldReportProps {
  propertyId: string;
  propertyName: string;
  onClose: () => void;
  onSuccess?: () => void; // Added callback
}

export default function FieldReportModal({ propertyId, propertyName, onClose, onSuccess }: FieldReportProps) {
  const { submitReport, loading } = useFieldReport();
  const [step, setStep] = useState<'form' | 'success'>('form');
  const [earnedPoints, setEarnedPoints] = useState(0);

  // Form State
  const [status, setStatus] = useState<string>('active');
  const [condition, setCondition] = useState<number>(3);
  const [notes, setNotes] = useState('');

  const handleSubmit = async () => {
    const result = await submitReport(propertyId, propertyName, { status, condition, notes });
    if (result.success) {
      setEarnedPoints(result.earned || 0);
      setStep('success');
      
      // AUTO-CLOSE LOGIC
      setTimeout(() => {
        if (onSuccess) onSuccess(); // Trigger Toast in parent
        onClose(); // Clear screen
      }, 2000); // 2 second delay to read the "Success" screen
    }
  };

  return (
    <div className="fixed inset-0 z-[150] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-md bg-[#111] border border-white/10 rounded-2xl overflow-hidden shadow-2xl relative"
      >
        {/* CLOSE BUTTON */}
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors z-20">
          <X size={20} />
        </button>

        <AnimatePresence mode="wait">
          
          {/* --- FORM STEP --- */}
          {step === 'form' && (
            <motion.div 
              key="form"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="p-6 md:p-8"
            >
              <div className="flex items-center gap-3 mb-6 border-b border-white/10 pb-4">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-500">
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white tracking-tight">Verify Asset</h2>
                  <p className="text-xs text-gray-400 font-mono truncate max-w-[200px]">{propertyName}</p>
                </div>
              </div>

              <div className="space-y-6">
                {/* 1. STATUS CHECK */}
                <div className="space-y-3">
                  <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Visual Status</label>
                  <div className="grid grid-cols-3 gap-2">
                    {['active', 'vacant', 'construction'].map((s) => (
                      <button
                        key={s}
                        onClick={() => setStatus(s)}
                        className={`px-2 py-3 rounded-lg border text-xs font-bold uppercase transition-all ${
                          status === s 
                            ? 'bg-emerald-500 text-black border-emerald-500' 
                            : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 2. CONDITION RATING */}
                <div className="space-y-3">
                  <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Asset Condition</label>
                  <div className="flex gap-2 justify-center bg-white/5 p-3 rounded-lg border border-white/10">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button 
                        key={star} 
                        onClick={() => setCondition(star)}
                        className="transition-transform hover:scale-110 active:scale-95"
                      >
                        <Star 
                          size={24} 
                          className={star <= condition ? "fill-yellow-400 text-yellow-400" : "text-gray-600"} 
                        />
                      </button>
                    ))}
                  </div>
                </div>

                {/* 3. INTEL NOTES */}
                <div className="space-y-2">
                  <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Field Notes</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="e.g. Road is unpaved, heavy construction noise..."
                    className="w-full bg-black border border-white/20 rounded-lg p-3 text-sm text-white focus:border-emerald-500 focus:outline-none min-h-[80px]"
                  />
                </div>

                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold rounded-xl uppercase tracking-widest text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-900/20"
                >
                  {loading ? 'Transmitting...' : 'Submit Report'}
                </button>
              </div>
            </motion.div>
          )}

          {/* --- SUCCESS STEP --- */}
          {step === 'success' && (
            <motion.div 
              key="success"
              initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
              className="p-8 flex flex-col items-center justify-center text-center min-h-[400px]"
            >
              <div className="relative mb-6">
                 <div className="absolute inset-0 bg-emerald-500 blur-2xl opacity-20 rounded-full animate-pulse" />
                 <CheckCircle size={64} className="text-emerald-500 relative z-10" />
              </div>
              
              <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-2">Intel Verified</h2>
              <p className="text-gray-400 text-sm mb-8">Transmission Successful.</p>

              <div className="bg-[#0A0A0A] border border-emerald-500/30 rounded-xl p-6 w-full mb-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-2 opacity-10"><ShieldCheck size={80} /></div>
                <p className="text-[10px] text-emerald-500 uppercase font-bold tracking-widest mb-1">Reputation Update</p>
                <div className="text-4xl font-black text-white flex items-center justify-center gap-1">
                  +{earnedPoints} <span className="text-sm font-bold text-gray-500 mt-3">XP</span>
                </div>
              </div>

              <p className="text-[10px] text-gray-500 animate-pulse">
                Closing interface...
              </p>
            </motion.div>
          )}

        </AnimatePresence>
      </motion.div>
    </div>
  );
}
