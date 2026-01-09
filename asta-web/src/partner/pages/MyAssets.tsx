import React, { useEffect, useState } from "react";
import { supabase } from "../../supabaseClient";
import { useAuth } from "../../hooks/useAuth";
import {
  Building,
  MapPin,
  Search,
  Filter,
  ExternalLink,
  Eye,
  MoreHorizontal,
} from "lucide-react";

export default function MyAssets() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [listings, setListings] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    if (user) fetchInventory();
  }, [user]);

  async function fetchInventory() {
    // 1. Get Partner ID
    const { data: profile } = await supabase
      .from("profiles")
      .select("partner_id")
      .eq("id", user?.id)
      .single();

    if (!profile?.partner_id) {
      setLoading(false);
      return; // Not a partner
    }

    // 2. Fetch Listings for this Partner
    const { data: properties, error } = await supabase
      .from("properties")
      .select("*")
      .eq("partner_id", profile.partner_id)
      .order("created_at", { ascending: false });

    if (!error && properties) {
      setListings(properties);
    }
    setLoading(false);
  }

  // --- FILTERS ---
  const filteredListings = listings.filter((item) => {
    const matchesSearch =
      item.title?.toLowerCase().includes(search.toLowerCase()) ||
      item.location_name?.toLowerCase().includes(search.toLowerCase());

    const matchesStatus =
      statusFilter === "all" || item.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  if (loading)
    return (
      <div className="p-8 text-emerald-500 font-mono animate-pulse">
        Syncing Inventory Database...
      </div>
    );

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Building className="text-blue-500" size={24} />
            Asset Inventory
          </h1>
          <p className="text-xs text-gray-500 font-mono uppercase tracking-widest mt-1">
            Total Assets: {listings.length} // Live Value: $
            {listings
              .reduce((acc, curr) => acc + (curr.price || 0), 0)
              .toLocaleString()}
          </p>
        </div>

        {/* CONTROLS */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-2.5 text-gray-500 w-4 h-4" />
            <input
              type="text"
              placeholder="Search address, title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#111] border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
          </div>
          <div className="flex bg-[#111] border border-white/10 rounded-lg p-1">
            {["all", "active", "draft"].map((filter) => (
              <button
                key={filter}
                onClick={() => setStatusFilter(filter)}
                className={`px-3 py-1.5 text-[10px] uppercase font-bold rounded transition-all ${
                  statusFilter === filter
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* LISTINGS GRID */}
      {filteredListings.length === 0 ? (
        <div className="border border-dashed border-white/10 rounded-xl p-12 text-center bg-white/5">
          <Building size={48} className="mx-auto text-gray-600 mb-4" />
          <h3 className="text-white font-bold">No Assets Found</h3>
          <p className="text-gray-500 text-sm mt-1">
            Upload inventory via the Partner Ops CSV tool or contact Admin.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredListings.map((item) => (
            <div
              key={item.id}
              className="bg-[#111] border border-white/10 rounded-xl overflow-hidden hover:border-emerald-500/30 transition-all group"
            >
              {/* IMAGE HEADER */}
              <div className="h-40 bg-gray-800 relative">
                <img
                  src={
                    item.image_urls?.[0] ||
                    "https://images.unsplash.com/photo-1600596542815-e3289047458b?auto=format&fit=crop&w=800"
                  }
                  alt={item.title}
                  className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                />
                <div className="absolute top-3 right-3 flex gap-2">
                  <span
                    className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider backdrop-blur-md ${
                      item.status === "active"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-gray-900/50 text-gray-400 border border-white/10"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
              </div>

              {/* CONTENT */}
              <div className="p-5">
                <h3
                  className="text-white font-bold truncate"
                  title={item.title}
                >
                  {item.title}
                </h3>
                <div className="flex items-center gap-1 text-gray-500 text-xs mt-1 mb-3">
                  <MapPin size={12} />
                  {item.location_name}
                </div>

                <div className="flex justify-between items-end border-t border-white/5 pt-3">
                  <div>
                    <p className="text-[10px] text-gray-500 uppercase font-mono">
                      List Price
                    </p>
                    <p className="text-lg font-bold text-blue-400">
                      {item.currency} {item.price?.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-gray-500 uppercase font-mono">
                      Views
                    </p>
                    <div className="flex items-center justify-end gap-1 text-gray-300 font-bold text-sm">
                      <Eye size={12} className="text-emerald-500" />
                      {Math.floor(Math.random() * 50) + 12} {/* Mock Stat */}
                    </div>
                  </div>
                </div>
              </div>

              {/* FOOTER ACTIONS */}
              <div className="bg-[#050505] border-t border-white/5 p-3 flex justify-between items-center">
                <span className="text-[10px] text-gray-600 font-mono">
                  REF:{" "}
                  {item.details?.external_id || item.id.toString().slice(0, 6)}
                </span>
                <div className="flex gap-2">
                  <button className="p-1.5 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors">
                    <ExternalLink size={14} />
                  </button>
                  <button className="p-1.5 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors">
                    <MoreHorizontal size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
