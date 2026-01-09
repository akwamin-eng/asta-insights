import { useEffect, useState } from "react";
import { Outlet, useNavigate, Link, useLocation } from "react-router-dom";
import { supabase } from "../../supabaseClient";
import { useAuth } from "../../hooks/useAuth";
import {
  LayoutDashboard,
  Building,
  Users,
  Settings,
  LogOut,
  Menu,
  ShieldAlert, // 👈 Added Icon
} from "lucide-react";

export default function PartnerLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [partnerName, setPartnerName] = useState<string | null>(null);

  // 🟢 INTERNAL USER CHECK
  const isInternal = user?.email?.endsWith("@asta.homes");

  useEffect(() => {
    async function checkPartnerStatus() {
      if (!user) {
        setPartnerName("Dev Preview Mode");
        setLoading(false);
        return;
      }

      // 1. Get user profile
      const { data: profile } = await supabase
        .from("profiles")
        .select("partner_id")
        .eq("id", user.id)
        .single();

      // --- BYPASS START (Keep for Dev) ---
      /*
      if (!profile?.partner_id) {
        navigate("/");
        return;
      }
      */
      // --- BYPASS END ---

      // 2. Get Partner Name
      let fetchedName = "Dev Partner Inc.";
      if (profile?.partner_id) {
        const { data: partner } = await supabase
          .from("partners")
          .select("name")
          .eq("id", profile.partner_id)
          .single();
        if (partner) fetchedName = partner.name;
      }

      setPartnerName(fetchedName);
      setLoading(false);
    }

    checkPartnerStatus();
  }, [user, navigate]);

  if (loading)
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-emerald-500 font-mono text-xs uppercase tracking-widest">
        <span className="animate-pulse">Initializing Protocol...</span>
      </div>
    );

  return (
    <div className="min-h-screen bg-[#050505] flex text-gray-300 font-sans selection:bg-emerald-500/30">
      {/* SIDEBAR */}
      <aside className="w-64 bg-[#111] border-r border-white/10 flex flex-col">
        {/* Brand Header */}
        <div className="p-6 border-b border-white/5">
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Asta<span className="text-emerald-500">Partner</span>
          </h2>
          <div className="mt-2 flex items-center gap-2 px-2 py-1 bg-white/5 rounded border border-white/5">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <p className="text-[10px] text-gray-400 font-mono uppercase tracking-widest truncate">
              {partnerName}
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-1">
          <NavItem
            to="/partner"
            icon={<LayoutDashboard size={18} />}
            label="Dashboard"
            isActive={location.pathname === "/partner"}
          />
          <NavItem
            to="/partner/listings"
            icon={<Building size={18} />}
            label="My Assets"
            isActive={location.pathname.startsWith("/partner/listings")}
          />
          <NavItem
            to="/partner/leads"
            icon={<Users size={18} />}
            label="Leads & Hunters"
            isActive={location.pathname.startsWith("/partner/leads")}
          />
          <NavItem
            to="/partner/settings"
            icon={<Settings size={18} />}
            label="Protocol Settings"
            isActive={location.pathname.startsWith("/partner/settings")}
          />
        </nav>

        {/* Footer / User Info */}
        <div className="p-4 border-t border-white/5 space-y-1">
          {/* 🟢 ASTA TOWER SHORTCUT (Internal Only) */}
          {isInternal && (
            <button
              onClick={() => navigate("/admin/dashboard")}
              className="flex items-center gap-3 w-full px-3 py-2 text-xs font-mono text-purple-400 hover:text-white hover:bg-purple-500/10 rounded transition-colors group mb-2"
            >
              <ShieldAlert
                size={14}
                className="group-hover:text-purple-300 transition-colors"
              />
              <span>RETURN TO TOWER</span>
            </button>
          )}

          <button className="flex items-center gap-3 w-full px-3 py-2 text-xs font-mono text-gray-500 hover:text-white transition-colors group hover:bg-white/5 rounded">
            <LogOut
              size={14}
              className="group-hover:text-red-400 transition-colors"
            />
            <span>TERMINATE SESSION</span>
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-y-auto custom-scrollbar">
        {/* We wrap Outlet in a div to ensure consistent padding/styling if needed */}
        <div className="min-h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

// Sub-component for cleaner nav links
function NavItem({
  to,
  icon,
  label,
  isActive,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
}) {
  return (
    <Link
      to={to}
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 border border-transparent
        ${
          isActive
            ? "bg-emerald-900/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]"
            : "text-gray-400 hover:text-white hover:bg-white/5"
        }
      `}
    >
      <span className={isActive ? "text-emerald-500" : "text-gray-500"}>
        {icon}
      </span>
      {label}
    </Link>
  );
}
