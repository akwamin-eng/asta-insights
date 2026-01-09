import React from 'react';

export default function MapOnboarding({ onComplete }: { onComplete: () => void }) {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-[#1A1A1A] p-6 rounded-xl border border-white/10 max-w-md text-center shadow-2xl">
        <h2 className="text-xl font-bold text-white mb-2 tracking-wide">SYSTEM ONLINE</h2>
        <p className="text-gray-400 mb-6 text-sm">
          Welcome to the Asta Registry. Use the map to explore Verified Land and Property Intelligence.
        </p>
        <button
          onClick={onComplete}
          className="bg-emerald-500 hover:bg-emerald-400 text-black px-6 py-2 rounded-lg font-bold transition-all uppercase tracking-wider text-xs"
        >
          Initialize
        </button>
      </div>
    </div>
  );
}
