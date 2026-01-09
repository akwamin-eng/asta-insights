import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle } from 'lucide-react';

interface ToastProps {
  message: string;
  type?: 'success' | 'error';
  onClose: () => void;
}

export default function Toast({ message, type = 'success', onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[300] pointer-events-none">
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.9 }}
        className={`bg-[#0A0A0A] border ${
          type === 'success' ? 'border-emerald-500/50 text-emerald-500' : 'border-red-500/50 text-red-500'
        } px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 min-w-[300px] justify-center backdrop-blur-md`}
      >
        {type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
        <span className="text-xs font-bold uppercase tracking-widest text-white">
          {message}
        </span>
      </motion.div>
    </div>
  );
}
