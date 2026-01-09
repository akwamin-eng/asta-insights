import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { supabase } from "../supabaseClient";
import {
  Building,
  MapPin,
  ShieldCheck,
  ExternalLink,
  ArrowLeft,
} from "lucide-react";
import { PageReveal } from "../components/ui/PageReveal";

export default function PublicPartnerProfile() {
  const { slug } = useParams();
  const [partner, setPartner] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (slug) fetchPartnerData();
  }, [slug]);

  async function fetchPartnerData() {
    setLoading(true);

    // 1. Fetch Partner by Slug
    const { data: partnerData, error } = await supabase
      .from("partners")
      .select("*")
      .eq("slug", slug)
      .eq("status", "active") // Only active partners
      .single();

    if (error || !partnerData) {
      setLoading(false);
      return;
    }

    setPartner(partnerData);

    // 2. Fetch Active Listings
    const { data: properties } = await supabase
      .from("properties")
      .select("*")
      .eq("partner_id", partnerData.id)
      .eq("status", "active") // Only active listings
      .order("created_at", { ascending: false });

    if (properties) setListings(properties);
    setLoading(false);
  }

  if (loading)
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-emerald-500 font-mono animate-pulse">
        ESTABLISHING UPLINK...
      </div>
    );

  if (!partner)
    return (
      <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center text-gray-500 gap-4">
        <Building size={48} className="text-gray-700" />
        <h1 className="text-xl font-bold text-gray-300">Partner Not Found</h1>
        <Link to="/" className="text-emerald-500 hover:underline">
          Return to Asta Map
        </Link>
      </div>
    );

  return (
    <PageReveal className="min-h-screen bg-[#050505] text-gray-300 font-sans">
      {/* HEADER HERO */}
      <div className="h-64 bg-gradient-to-b from-emerald-900/20 to-[#050505] border-b border-white/10 relative">
        <div className="absolute inset-0 tactical-grid opacity-30" />
        <div className="max-w-7xl mx-auto px-6 h-full flex flex-col justify-end pb-8 relative z-10">
          <Link
            to="/"
            className="absolute top-6 left-6 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-gray-500 hover:text-white transition-colors"
          >
            <ArrowLeft size={14} /> Back to Grid
          </Link>

          <div className="flex items-end gap-6">
            <div className="w-24 h-24 bg-[#111] border border-white/10 rounded-xl flex items-center justify-center shadow-2xl">
              <Building size={40} className="text-emerald-500" />
            </div>
            <div className="mb-2">
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-white tracking-tight">
                  {partner.name}
                </h1>
                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                  <ShieldCheck size={12} /> Verified Partner
                </span>
              </div>
              <p className="text-gray-500 text-sm mt-1 flex items-center gap-4">
                <span>{listings.length} Active Listings</span>
                {partner.contact_email && (
                  <span className="text-gray-600">
                    | {partner.contact_email}
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* LISTINGS GRID */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {listings.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-white/10 rounded-xl bg-white/5">
            <p className="text-gray-500">
              No active inventory available at this time.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {listings.map((item) => (
              <div
                key={item.id}
                className="bg-[#111] border border-white/10 rounded-xl overflow-hidden hover:border-emerald-500/30 transition-all group hover:-translate-y-1 duration-300 shadow-xl"
              >
                {/* Image */}
                <div className="h-48 bg-gray-800 relative overflow-hidden">
                  <img
                    src={
                      item.image_urls?.[0] ||
                      "https://images.unsplash.com/photo-1600596542815-e3289047458b?auto=format&fit=crop&w=800"
                    }
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-60" />
                  <div className="absolute bottom-3 left-3 text-white">
                    <p className="text-lg font-bold">
                      {item.currency} {item.price?.toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Details */}
                <div className="p-5">
                  <h3 className="text-white font-bold truncate mb-1">
                    {item.title}
                  </h3>
                  <p className="text-xs text-gray-500 flex items-center gap-1 mb-4">
                    <MapPin size={12} /> {item.location_name}
                  </p>

                  <div className="flex justify-between items-center pt-4 border-t border-white/5">
                    <div className="text-xs text-gray-400 font-mono">
                      {item.details?.bedrooms} BD | {item.details?.bathrooms} BA
                    </div>
                    <button className="text-[10px] font-bold uppercase tracking-wider bg-white/5 hover:bg-white/10 text-white px-3 py-1.5 rounded transition-colors flex items-center gap-2">
                      View Asset <ExternalLink size={12} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageReveal>
  );
}
