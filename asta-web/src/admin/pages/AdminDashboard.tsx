import React, { useEffect, useState } from "react";
import { supabase } from "../../lib/supabase";
import {
  Activity,
  Database,
  Users,
  Bug,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  Terminal,
  MessageCircle,
  Phone,
  Zap,
  ShieldAlert,
  Map as MapIcon,
  X,
} from "lucide-react";
import ConflictResolver from "../../components/admin/ConflictResolver"; // 👈 Import the Resolver

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    users: 0,
    assets: 0,
    bugs: 0,
    leads: 0,
    conflicts: 0, // 👈 New Stat
  });
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [latency, setLatency] = useState<number | null>(null);

  // 🟢 NEW: State for opening the Conflict Resolver Modal
  const [resolvingTicket, setResolvingTicket] = useState<any>(null);

  useEffect(() => {
    fetchPulse();
  }, []);

  async function fetchPulse() {
    setLoading(true);
    const start = performance.now();

    // 1. Parallel Count Fetching
    const [
      { count: userCount },
      { count: assetCount },
      { count: bugCount },
      { count: leadCount },
      { count: conflictCount }, // 👈 Fetch Ticket Count
    ] = await Promise.all([
      supabase.from("profiles").select("*", { count: "exact", head: true }),
      supabase.from("properties").select("*", { count: "exact", head: true }),
      supabase
        .from("bug_reports")
        .select("*", { count: "exact", head: true })
        .eq("status", "open"),
      supabase.from("leads").select("*", { count: "exact", head: true }),
      supabase
        .from("admin_tickets")
        .select("*", { count: "exact", head: true })
        .eq("status", "open"),
    ]);

    const end = performance.now();
    setLatency(Math.round(end - start));

    setStats({
      users: userCount || 0,
      assets: assetCount || 0,
      bugs: bugCount || 0,
      leads: leadCount || 0,
      conflicts: conflictCount || 0,
    });

    // 2. Fetch Combined Activity Feed

    // A. Bugs
    const { data: bugs } = await supabase
      .from("bug_reports")
      .select(
        "id, created_at, description, category, status, profiles:user_id(email)"
      )
      .eq("status", "open") // Only show open bugs in feed
      .order("created_at", { ascending: false })
      .limit(5);

    // B. Leads
    const { data: leads } = await supabase
      .from("leads")
      .select("id, created_at, type, properties:property_id(title)")
      .order("created_at", { ascending: false })
      .limit(5);

    // C. Land Conflicts (Tickets) 👈 NEW
    const { data: tickets } = await supabase
      .from("admin_tickets")
      .select("*")
      .eq("status", "open")
      .order("created_at", { ascending: false });

    // Combine and sort
    const combined = [
      ...(tickets || []).map((t) => ({ ...t, feedType: "ticket" })), // Priority
      ...(bugs || []).map((b) => ({ ...b, feedType: "bug" })),
      ...(leads || []).map((l) => ({ ...l, feedType: "lead" })),
    ]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      .slice(0, 15); // Increased limit to show conflicts

    setActivityFeed(combined);
    setLoading(false);
  }

  const resolveBug = async (id: number) => {
    // Optimistic Update
    setActivityFeed((prev) =>
      prev.filter((item) => item.id !== id || item.feedType !== "bug")
    );
    await supabase
      .from("bug_reports")
      .update({ status: "resolved" })
      .eq("id", id);
    fetchPulse(); // Refresh counts
  };

  const handleTicketResolved = () => {
    setResolvingTicket(null);
    fetchPulse(); // Refresh feed to remove the resolved ticket
  };

  return (
    <div className="space-y-8 relative">
      {/* HEADER */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
            <Terminal size={24} className="text-emerald-500" />
            System Pulse
          </h2>
          <p className="text-gray-500 text-xs font-mono">
            Real-time telemetry from Asta Network
          </p>
        </div>
        <div className="flex items-center gap-4">
          {latency && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono text-gray-400">
              <Zap
                size={12}
                className={
                  latency < 200 ? "text-emerald-500" : "text-yellow-500"
                }
              />
              {latency}ms latency
            </div>
          )}
          <button
            onClick={fetchPulse}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
            title="Force Refresh Data Streams"
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* KPI GRID */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* CONFLICTS (High Priority) */}
        <div
          className={`bg-[#111] border p-5 rounded-xl relative overflow-hidden group ${
            stats.conflicts > 0
              ? "border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]"
              : "border-white/10"
          }`}
        >
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <ShieldAlert size={64} className="text-red-500" />
          </div>
          <div className="flex justify-between items-start mb-4">
            <ShieldAlert className="text-red-500 w-5 h-5" />
            <span className="text-[10px] text-red-500 font-mono uppercase bg-red-500/10 px-2 py-0.5 rounded animate-pulse">
              Critical
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white">{stats.conflicts}</h3>
          <p className="text-xs text-gray-500 mt-1">Active Land Disputes</p>
        </div>

        {/* USERS */}
        <div className="bg-[#111] border border-white/10 p-5 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Users size={64} />
          </div>
          <div className="flex justify-between items-start mb-4">
            <Users className="text-blue-500 w-5 h-5" />
            <span className="text-[10px] text-gray-500 font-mono uppercase bg-blue-500/10 px-2 py-0.5 rounded">
              Operatives
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white">{stats.users}</h3>
          <p className="text-xs text-gray-500 mt-1">Total Profiles</p>
        </div>

        {/* ASSETS */}
        <div className="bg-[#111] border border-white/10 p-5 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Database size={64} />
          </div>
          <div className="flex justify-between items-start mb-4">
            <Database className="text-purple-500 w-5 h-5" />
            <span className="text-[10px] text-gray-500 font-mono uppercase bg-purple-500/10 px-2 py-0.5 rounded">
              Inventory
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white">{stats.assets}</h3>
          <p className="text-xs text-gray-500 mt-1">Properties Mapped</p>
        </div>

        {/* LEADS */}
        <div className="bg-[#111] border border-white/10 p-5 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <MessageCircle size={64} />
          </div>
          <div className="flex justify-between items-start mb-4">
            <MessageCircle className="text-emerald-500 w-5 h-5" />
            <span className="text-[10px] text-gray-500 font-mono uppercase bg-emerald-500/10 px-2 py-0.5 rounded">
              Conversion
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white">{stats.leads}</h3>
          <p className="text-xs text-gray-500 mt-1">Actions</p>
        </div>

        {/* BUGS */}
        <div className="bg-[#111] border border-white/10 p-5 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Bug size={64} />
          </div>
          <div className="flex justify-between items-start mb-4">
            <Bug className="text-orange-500 w-5 h-5" />
            <span className="text-[10px] text-gray-500 font-mono uppercase bg-orange-500/10 px-2 py-0.5 rounded">
              Signals
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white">{stats.bugs}</h3>
          <p className="text-xs text-gray-500 mt-1">Open Bugs</p>
        </div>
      </div>

      {/* LIVE ACTIVITY STREAM */}
      <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden flex flex-col min-h-[400px]">
        <div className="p-5 border-b border-white/10 bg-white/[0.02] flex justify-between items-center">
          <div>
            <h3 className="text-white font-bold text-sm uppercase tracking-wider">
              Live Pipeline
            </h3>
            <p className="text-xs text-gray-500">
              Conflicts, Signals & Conversions
            </p>
          </div>
          <div className="text-[10px] bg-red-900/20 text-red-400 border border-red-500/20 px-2 py-1 rounded flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
            LIVE
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-black/20 text-[10px] uppercase text-gray-500 font-bold tracking-widest">
              <tr>
                <th className="p-4 w-32">Type</th>
                <th className="p-4">Intelligence Detail</th>
                <th className="p-4 w-32">Time</th>
                <th className="p-4 w-24 text-right">Command</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-xs">
              {loading ? (
                <tr>
                  <td
                    colSpan={4}
                    className="p-8 text-center text-gray-500 italic"
                  >
                    Decrypting stream...
                  </td>
                </tr>
              ) : activityFeed.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="p-8 text-center text-gray-600 font-mono"
                  >
                    NO ACTIVITY DETECTED
                  </td>
                </tr>
              ) : (
                activityFeed.map((item, i) => (
                  <tr
                    key={`${item.feedType}-${item.id}`}
                    className={`hover:bg-white/[0.02] transition-colors ${
                      item.status === "resolved" ? "opacity-30" : ""
                    } ${
                      item.feedType === "ticket"
                        ? "bg-red-900/5 hover:bg-red-900/10"
                        : ""
                    }`}
                  >
                    {/* TYPE COLUMN */}
                    <td className="p-4">
                      {item.feedType === "ticket" ? (
                        <span className="px-2 py-1 rounded border text-[9px] font-bold uppercase bg-red-500/20 text-red-400 border-red-500/30 flex w-fit items-center gap-1 animate-pulse">
                          <ShieldAlert size={10} /> LAND DISPUTE
                        </span>
                      ) : item.feedType === "bug" ? (
                        <span className="px-2 py-1 rounded border text-[9px] font-bold uppercase bg-orange-500/10 text-orange-400 border-orange-500/20 flex w-fit items-center gap-1">
                          <Bug size={10} /> {item.category || "BUG"}
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded border text-[9px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border-emerald-500/20 flex w-fit items-center gap-1">
                          {item.type === "call" ? (
                            <Phone size={10} />
                          ) : (
                            <MessageCircle size={10} />
                          )}{" "}
                          LEAD
                        </span>
                      )}
                    </td>

                    {/* DETAIL COLUMN */}
                    <td className="p-4 text-gray-300">
                      {item.feedType === "ticket" ? (
                        <div className="flex flex-col">
                          <span className="font-bold text-white flex items-center gap-2">
                            <MapIcon size={12} className="text-red-400" />
                            Overlap Detected:{" "}
                            {item.conflict_details?.overlap_count} Listings
                          </span>
                          <span className="text-[10px] text-gray-500">
                            Property ID: {item.property_id} • Priority:{" "}
                            {item.priority}
                          </span>
                        </div>
                      ) : item.feedType === "bug" ? (
                        <div className="flex flex-col">
                          <span className="font-mono text-gray-300">
                            {item.description}
                          </span>
                          <span className="text-[10px] text-gray-600">
                            User: {item.profiles?.email || "Anon"}
                          </span>
                        </div>
                      ) : (
                        <div className="flex flex-col">
                          <span className="font-bold text-white">
                            Interest:{" "}
                            {item.properties?.title || "Unknown Property"}
                          </span>
                          <span className="text-[10px] text-gray-500">
                            Via: {item.type.toUpperCase()}
                          </span>
                        </div>
                      )}
                    </td>

                    {/* TIME COLUMN */}
                    <td className="p-4 text-gray-500 font-mono text-[10px]">
                      {new Date(item.created_at).toLocaleTimeString()} <br />
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>

                    {/* ACTION COLUMN */}
                    <td className="p-4 text-right">
                      {item.feedType === "ticket" && item.status === "open" && (
                        <button
                          onClick={() => setResolvingTicket(item)}
                          className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded text-[10px] font-bold uppercase shadow-lg shadow-red-900/20 transition-all hover:scale-105"
                        >
                          Resolve
                        </button>
                      )}
                      {item.feedType === "bug" && item.status === "open" && (
                        <button
                          onClick={() => resolveBug(item.id)}
                          className="p-1.5 hover:bg-emerald-500/20 text-gray-400 hover:text-emerald-500 rounded transition-colors"
                          title="Mark Resolved"
                        >
                          <CheckCircle2 size={16} />
                        </button>
                      )}
                      {item.feedType === "lead" && (
                        <span className="text-[10px] text-gray-600 font-mono">
                          LOGGED
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 🔴 CONFLICT RESOLVER MODAL */}
      {resolvingTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-4xl relative">
            <button
              onClick={() => setResolvingTicket(null)}
              className="absolute -top-10 right-0 text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>

            <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
              <div className="p-4 border-b border-white/10 flex items-center gap-3 bg-red-900/10">
                <ShieldAlert className="text-red-500" />
                <div>
                  <h3 className="text-lg font-bold text-white">
                    War Room: Conflict Resolution
                  </h3>
                  <p className="text-xs text-gray-400">
                    Review geospatial overlap and adjudicate ownership.
                  </p>
                </div>
              </div>

              {/* MOUNT THE MAP RESOLVER */}
              <ConflictResolver
                ticketId={resolvingTicket.id}
                propertyId={resolvingTicket.property_id}
                onResolve={handleTicketResolved}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
