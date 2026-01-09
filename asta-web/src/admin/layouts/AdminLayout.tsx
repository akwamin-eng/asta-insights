import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Building, 
  Users, 
  Briefcase,
  BarChart3, // 👈 New Icon for Reports
  LogOut, 
  ShieldCheck 
} from 'lucide-react';
import { supabase } from '../../lib/supabase';

export default function AdminLayout() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Mission Control', path: '/admin/dashboard' },
    { icon: Building, label: 'Asset Governance', path: '/admin/assets' },
    { icon: Users, label: 'User Command', path: '/admin/users' },
    { icon: Briefcase, label: 'Partner Ops', path: '/admin/partner-ops' },
    { icon: BarChart3, label: 'Intelligence', path: '/admin/reports' }, // 👈 Added
  ];

  return (
    <div className="flex h-screen bg-[#09090b] text-gray-100 font-sans selection:bg-purple-500 selection:text-white">
      
      {/* SIDEBAR */}
      <aside className="w-64 border-r border-white/10 flex flex-col bg-black/50 backdrop-blur-xl">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-purple-600 rounded flex items-center justify-center">
              <ShieldCheck className="text-white w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-widest uppercase">Asta Tower</h1>
              <p className="text-[10px] text-gray-500">Admin Clearance: Level 5</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                  isActive 
                    ? 'bg-purple-600/10 text-purple-400 border border-purple-600/20' 
                    : 'text-gray-500 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-xs font-bold uppercase tracking-wider text-red-400 hover:bg-red-900/10 hover:text-red-300 transition-colors"
          >
            <LogOut size={18} />
            Secure Logout
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-auto bg-[#050505]">
        <div className="max-w-7xl mx-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
