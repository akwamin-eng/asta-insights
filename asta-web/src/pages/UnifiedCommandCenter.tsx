import React, { useState } from 'react';
import { LayoutDashboard, Globe, Radio, Map as MapIcon } from 'lucide-react';
import Dashboard from '../components/Dashboard';
import PropertyFeed from '../components/PropertyFeed';
import LandPlotter from '../components/LandPlotter';

export default function UnifiedCommandCenter() {
  // 'dashboard' | 'feed' | 'plotter'
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="flex h-screen bg-[#0A0A0A] text-white overflow-hidden font-sans">
      
      {/* SIDEBAR (Simplified for Focus) */}
      <div className="w-20 border-r border-white/10 flex flex-col items-center py-6 gap-8 bg-black/40 backdrop-blur-xl z-20">
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <span className="font-bold text-lg">A</span>
        </div>

        <nav className="flex flex-col gap-4">
          <NavButton 
            active={activeTab === 'dashboard'} 
            onClick={() => setActiveTab('dashboard')} 
            icon={<LayoutDashboard size={20} />} 
            label="Dash" 
          />
          <NavButton 
            active={activeTab === 'feed'} 
            onClick={() => setActiveTab('feed')} 
            icon={<Radio size={20} />} 
            label="Intel" 
          />
          <NavButton 
            active={activeTab === 'plotter'} 
            onClick={() => setActiveTab('plotter')} 
            icon={<MapIcon size={20} />} 
            label="Plotter" 
          />
        </nav>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        
        {/* HEADER */}
        <header className="h-16 border-b border-white/5 bg-black/20 backdrop-blur-md flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-3">
            <Globe className="text-indigo-500 animate-pulse" size={18} />
            <h1 className="font-bold text-lg tracking-tight">
              {activeTab === 'dashboard' && 'Command Center'}
              {activeTab === 'feed' && 'Market Intelligence'}
              {activeTab === 'plotter' && 'Land Registry Engine'}
            </h1>
          </div>
          <div className="text-xs text-gray-500 font-mono">
            ASTA-OS v2.1 • ACCRA NODE
          </div>
        </header>

        {/* DYNAMIC VIEWPORT */}
        <main className="flex-1 overflow-y-auto bg-gradient-to-br from-[#0A0A0A] to-[#111] p-6 custom-scrollbar">
          
          {activeTab === 'dashboard' && (
            <div className="animate-in fade-in duration-500">
              <Dashboard />
            </div>
          )}

          {activeTab === 'feed' && (
            <div className="animate-in slide-in-from-right duration-500">
              <PropertyFeed />
            </div>
          )}

          {activeTab === 'plotter' && (
            <div className="animate-in zoom-in-95 duration-500 h-full">
              <LandPlotter />
            </div>
          )}

        </main>
      </div>
    </div>
  );
}

// Sub-component for nav buttons
function NavButton({ active, onClick, icon, label }: any) {
  return (
    <button
      onClick={onClick}
      className={`
        w-12 h-12 rounded-xl flex flex-col items-center justify-center gap-1 transition-all duration-300
        ${active 
          ? 'bg-white/10 text-white shadow-lg shadow-white/5 scale-105 border border-white/10' 
          : 'text-gray-500 hover:text-white hover:bg-white/5'}
      `}
    >
      {icon}
      <span className="text-[9px] font-medium uppercase tracking-wide">{label}</span>
    </button>
  );
}
