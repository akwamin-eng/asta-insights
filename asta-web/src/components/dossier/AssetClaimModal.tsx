import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, ShieldCheck, DownloadCloud, X } from 'lucide-react';

interface AssetClaimModalProps {
  count: number;
  onClaim: () => void;
  onIgnore: () => void;
  isSyncing: boolean;
}

export default function AssetClaimModal({ count, onClaim, onIgnore, isSyncing }: AssetClaimModalProps) {
  if (count === 0) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 sm:p-0 pointer-events-none">
        <motion.div 
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="bg-[#0f172a] border border-blue-500/30 rounded-lg shadow-[0_0_50px_rgba(59,130,246,0.2)] w-full max-w-md pointer-events-auto overflow-hidden"
        >
          {/* Header */}
          <div className="bg-blue-900/20 p-4 border-b border-blue-500/20 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Radio className="text-blue-400 animate-pulse" size={20} />
                <div className="absolute inset-0 bg-blue-400 blur-lg opacity-50 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Signal Intercepted</h3>
                <p className="text-[10px] text-blue-300">Identity Match Detected</p>
              </div>
            </div>
            <button onClick={onIgnore} className="text-gray-500 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>

          {/* Body */}
          <div className="p-6">
            <p className="text-gray-300 text-sm leading-relaxed mb-6">
              We detected <strong className="text-white">{count} asset{count > 1 ? 's' : ''}</strong> uploaded via WhatsApp linked to your secure line. 
              These assets are currently unassigned.
            </p>

            <div className="bg-blue-500/5 rounded border border-blue-500/10 p-3 mb-6 flex items-center gap-3">
              <ShieldCheck className="text-emerald-500 shrink-0" size={18} />
              <p className="text-[11px] text-gray-400">
                Syncing will transfer full command authority to this dossier.
              </p>
            </div>

            <div className="flex gap-3">
              <button 
                onClick={onIgnore}
                className="flex-1 py-3 bg-white/5 hover:bg-white/10 text-gray-400 text-xs font-bold uppercase tracking-wider rounded transition-colors"
              >
                Ignore
              </button>
              <button 
                onClick={onClaim}
                disabled={isSyncing}
                className="flex-[2] py-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold uppercase tracking-wider rounded shadow-lg shadow-blue-900/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSyncing ? (
                  <span className="animate-pulse">Syncing Database...</span>
                ) : (
                  <>
                    <DownloadCloud size={16} /> Sync {count} Assets
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
