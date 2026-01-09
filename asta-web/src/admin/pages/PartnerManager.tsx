import React, { useEffect, useState } from "react";
import { supabase } from "../../supabaseClient";
import {
  Building,
  Search,
  Plus,
  MoreHorizontal,
  ShieldCheck,
  AlertCircle,
  X,
  Users, // Added for potential future linking
} from "lucide-react";

export default function PartnerManager() {
  const [partners, setPartners] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Modal State
  const [isCreating, setIsCreating] = useState(false);
  const [newPartnerName, setNewPartnerName] = useState("");
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    fetchPartners();
  }, []);

  async function fetchPartners() {
    setLoading(true);
    const { data, error } = await supabase
      .from("partners")
      .select("*")
      .order("created_at", { ascending: false });

    if (!error && data) {
      setPartners(data);
    }
    setLoading(false);
  }

  // --- ACTIONS ---

  const handleCreatePartner = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError("");
    if (!newPartnerName.trim()) return;

    // 🟢 FORCE STATUS: ACTIVE
    // This ensures they appear in the User Manager dropdown immediately
    const { data, error } = await supabase
      .from("partners")
      .insert([{ name: newPartnerName, status: "active" }])
      .select()
      .single();

    if (error) {
      setCreateError(error.message);
    } else if (data) {
      setPartners([data, ...partners]);
      setNewPartnerName("");
      setIsCreating(false);
    }
  };

  const toggleStatus = async (id: string, currentStatus: string) => {
    const newStatus = currentStatus === "active" ? "suspended" : "active";

    // Optimistic Update
    setPartners((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: newStatus } : p))
    );

    await supabase.from("partners").update({ status: newStatus }).eq("id", id);
  };

  // --- FILTERING ---
  const filteredPartners = partners.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 relative">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">
            Partner Command
          </h2>
          <p className="text-gray-500 text-xs">
            Active Syndicates: {partners.length}
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-2.5 text-gray-500 w-4 h-4" />
            <input
              type="text"
              placeholder="Search Organizations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#111] border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-purple-500/50"
            />
          </div>

          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
          >
            <Plus size={16} />
            Add Partner
          </button>
        </div>
      </div>

      {/* PARTNER TABLE */}
      <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-white/10 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                <th className="p-4 w-12">Logo</th>
                <th className="p-4">Organization</th>
                <th className="p-4">Contract Date</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-gray-300">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    Scanning Database...
                  </td>
                </tr>
              ) : filteredPartners.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    No Partners Found.
                  </td>
                </tr>
              ) : (
                filteredPartners.map((partner) => (
                  <tr
                    key={partner.id}
                    className="hover:bg-white/[0.02] transition-colors group"
                  >
                    {/* AVATAR/LOGO PLACEHOLDER */}
                    <td className="p-4">
                      <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center border border-white/10 text-gray-600">
                        <Building size={18} />
                      </div>
                    </td>

                    {/* ORGANIZATION NAME */}
                    <td className="p-4">
                      <div className="font-bold text-white text-base">
                        {partner.name}
                      </div>
                      <div className="text-[10px] text-gray-600 font-mono uppercase">
                        {/* 🛑 GENTLE UPDATE: Removed .split('-') to prevent crash on number IDs */}
                        ID: {partner.id}
                      </div>
                    </td>

                    {/* DATE */}
                    <td className="p-4">
                      <div className="text-xs text-gray-400 font-mono">
                        {new Date(partner.created_at).toLocaleDateString()}
                      </div>
                    </td>

                    {/* STATUS */}
                    <td className="p-4">
                      {partner.status === "active" ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold uppercase tracking-wider">
                          <ShieldCheck size={12} /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-bold uppercase tracking-wider">
                          <AlertCircle size={12} /> Suspended
                        </span>
                      )}
                    </td>

                    {/* ACTIONS */}
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() =>
                            toggleStatus(partner.id, partner.status)
                          }
                          className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white border border-white/10 hover:border-white/30 rounded transition-colors"
                        >
                          {partner.status === "active" ? "Suspend" : "Activate"}
                        </button>
                        <button className="p-2 text-gray-500 hover:text-white transition-colors">
                          <MoreHorizontal size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE MODAL OVERLAY */}
      {isCreating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#111] border border-white/10 rounded-xl w-full max-w-md p-6 shadow-2xl relative">
            <button
              onClick={() => setIsCreating(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-white"
            >
              <X size={20} />
            </button>

            <h3 className="text-lg font-bold text-white mb-1">
              Onboard New Partner
            </h3>
            <p className="text-xs text-gray-500 mb-6">
              Create a new organization entity.
            </p>

            <form onSubmit={handleCreatePartner} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                  Organization Name
                </label>
                <input
                  type="text"
                  autoFocus
                  placeholder="e.g. Acme Realty Group"
                  value={newPartnerName}
                  onChange={(e) => setNewPartnerName(e.target.value)}
                  className="w-full bg-black/50 border border-white/20 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>

              {createError && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-xs">
                  {createError}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-bold rounded-lg transition-all"
                >
                  Create Entity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
