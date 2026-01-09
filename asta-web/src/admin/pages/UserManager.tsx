import React, { useEffect, useState } from "react";
import { supabase } from "../../supabaseClient";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Search,
  UserCog,
  CheckCircle2,
  Ban,
  Mail,
  Smartphone,
} from "lucide-react";

export default function UserManager() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // 🟢 UPDATED FILTER STATE
  // Simplified: All | Internal | Public (Partners are considered 'Public' for this view)
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);

    // Fetch Users (Removed Partner Fetch logic)
    const { data: userData, error: userError } = await supabase
      .from("profiles")
      .select("*")
      .order("created_at", { ascending: false });

    if (!userError && userData) {
      setUsers(userData);
    }

    setLoading(false);
  }

  // --- ACTIONS ---

  const toggleRole = async (id: string, currentRole: string) => {
    const roles = ["user", "agent", "admin"];
    const nextIndex = (roles.indexOf(currentRole) + 1) % roles.length;
    const newRole = roles[nextIndex];

    if (!window.confirm(`Change role to ${newRole.toUpperCase()}?`)) return;

    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, role: newRole } : u))
    );

    const { error } = await supabase
      .from("profiles")
      .update({ role: newRole })
      .eq("id", id);

    if (error) alert("Failed to update role");
  };

  const toggleVerification = async (id: string, currentTier: number) => {
    const newTier = currentTier > 0 ? 0 : 1;

    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, verification_tier: newTier } : u))
    );

    await supabase
      .from("profiles")
      .update({ verification_tier: newTier })
      .eq("id", id);
  };

  // --- FILTERING LOGIC ---
  const filteredUsers = users.filter((user) => {
    // 1. Text Search
    const matchesSearch =
      user.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      user.email?.toLowerCase().includes(search.toLowerCase()) ||
      user.phone_number?.includes(search);

    // 2. Category Filter
    let matchesCategory = true;
    const isInternal =
      user.email?.endsWith("@asta.homes") || user.role === "admin";

    switch (filterType) {
      case "internal":
        matchesCategory = isInternal;
        break;
      case "public":
        matchesCategory = !isInternal;
        break;
      default:
        matchesCategory = true;
    }

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">User Command</h2>
          <p className="text-gray-500 text-xs">
            Network Size: {users.length} Records
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {/* SEARCH */}
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-2.5 text-gray-500 w-4 h-4" />
            <input
              type="text"
              placeholder="Find Operative..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#111] border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-purple-500/50"
            />
          </div>

          {/* 🟢 CATEGORY TABS (Removed specific 'Partner' filter) */}
          <div className="flex bg-[#111] border border-white/10 rounded-lg p-1">
            {[
              { id: "all", label: "ALL" },
              { id: "internal", label: "INTERNAL" },
              { id: "public", label: "PUBLIC/EXTERNAL" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilterType(tab.id)}
                className={`px-3 py-1.5 text-[10px] uppercase font-bold rounded transition-all ${
                  filterType === tab.id
                    ? "bg-purple-600/20 text-purple-400 shadow-sm"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* USER TABLE */}
      <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-white/10 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                <th className="p-4 w-12">Avatar</th>
                <th className="p-4">Identity</th>
                <th className="p-4">Role / Type</th>
                {/* Removed Syndicate Link Column */}
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-gray-300">
              {loading ? (
                <tr>
                  <td
                    colSpan={5}
                    className="p-8 text-center text-gray-500 animate-pulse"
                  >
                    Decrypting Personnel Records...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    No operatives found in this sector.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => {
                  // Helper logic for rendering row
                  const isInternal = user.email?.endsWith("@asta.homes");

                  return (
                    <tr
                      key={user.id}
                      className="hover:bg-white/[0.02] transition-colors group"
                    >
                      {/* AVATAR */}
                      <td className="p-4">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center border ${
                            isInternal
                              ? "border-purple-500/30 bg-purple-500/10"
                              : "border-white/10 bg-white/5"
                          }`}
                        >
                          {user.avatar_url ? (
                            <img
                              src={user.avatar_url}
                              alt=""
                              className="w-full h-full object-cover rounded-full"
                            />
                          ) : (
                            <span
                              className={`text-xs font-bold ${
                                isInternal ? "text-purple-400" : "text-gray-500"
                              }`}
                            >
                              {user.full_name?.[0] || "?"}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* NAME & CONTACT */}
                      <td className="p-4">
                        <div className="flex flex-col">
                          <span className="font-bold text-white flex items-center gap-2">
                            {user.full_name || "Unknown User"}
                            {isInternal && (
                              <Shield size={12} className="text-purple-500" />
                            )}
                          </span>
                          <div className="flex items-center gap-2 mt-1">
                            {user.email && (
                              <div className="flex items-center gap-1 text-[11px] text-gray-500">
                                <Mail size={10} /> {user.email}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* ROLE */}
                      <td className="p-4">
                        <div className="flex gap-2">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                              user.role === "admin"
                                ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                                : user.role === "agent"
                                ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                            }`}
                          >
                            {user.role || "user"}
                          </span>
                          {isInternal && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-900/20 text-purple-300 border border-purple-500/20">
                              HQ
                            </span>
                          )}
                        </div>
                      </td>

                      {/* STATUS */}
                      <td className="p-4">
                        <button
                          onClick={() =>
                            toggleVerification(
                              user.id,
                              user.verification_tier || 0
                            )
                          }
                          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors text-[10px] font-bold uppercase tracking-wider ${
                            user.verification_tier > 0
                              ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/20"
                              : "text-gray-600 border border-transparent hover:border-white/10 hover:text-gray-400"
                          }`}
                          title={
                            user.verification_tier > 0
                              ? "Revoke Verification"
                              : "Grant Verified Status"
                          }
                        >
                          {user.verification_tier > 0 ? (
                            <>
                              <CheckCircle2 size={12} /> Verified
                            </>
                          ) : (
                            "Unverified"
                          )}
                        </button>
                      </td>

                      {/* ACTIONS */}
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() =>
                              toggleRole(user.id, user.role || "user")
                            }
                            className="p-2 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors"
                            title="Cycle Role"
                          >
                            <UserCog size={14} />
                          </button>
                          <button
                            className="p-2 hover:bg-red-500/10 rounded text-gray-400 hover:text-red-500 transition-colors"
                            title="Ban User"
                          >
                            <Ban size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
