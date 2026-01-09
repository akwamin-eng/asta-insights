import React, { useState } from 'react';
import { Info, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MetricCardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  helperTitle: string;
  helperText: string;
  className?: string; // Allow custom sizing
}

export default function MetricCard({ title, icon, children, helperTitle, helperText, className = "" }: MetricCardProps) {
  const [showHelper, setShowHelper] = useState(false);

  return (
    <div className={`bg-white/5 border border-white/10 rounded-xl p-5 relative overflow-hidden flex flex-col ${className}`}>
      
      {/* HEADER */}
      <div className="flex items-center justify-between mb-4 relative z-10">
        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
          {icon} {title}
        </h3>
        <button 
          onClick={() => setShowHelper(!showHelper)}
          className="text-gray-600 hover:text-emerald-500 transition-colors"
        >
          <Info size={14} />
        </button>
      </div>

      {/* CONTENT (The Chart/Data) */}
      <div className="flex-1 relative z-0">
        {children}
      </div>

      {/* HELPER OVERLAY (The Education Layer) */}
      <AnimatePresence>
        {showHelper && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }} 
            exit={{ opacity: 0, y: 10 }}
            className="absolute inset-0 bg-[#0A0A0A]/95 backdrop-blur-sm z-20 p-5 flex flex-col justify-center text-center"
          >
            <button 
              onClick={() => setShowHelper(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-white"
            >
              <X size={16} />
            </button>
            <h4 className="text-emerald-400 font-bold text-sm mb-2 uppercase tracking-wide">
              {helperTitle}
            </h4>
            <p className="text-xs text-gray-300 leading-relaxed max-w-[90%] mx-auto">
              {helperText}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
