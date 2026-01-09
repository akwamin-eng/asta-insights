import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import {
  MapPin,
  Bed,
  Bath,
  Square,
  Share2,
  ArrowLeft,
  Phone,
  MessageCircle,
  ShieldCheck,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { motion } from "framer-motion";
import { trackEvent } from "../lib/analytics";

export default function ListingPage() {
  const { id } = useParams<{ id: string }>();
  const [property, setProperty] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [owner, setOwner] = useState<any>(null);

  useEffect(() => {
    async function fetchListing() {
      if (!id) return;

      const { data: propData, error: propError } = await supabase
        .from("properties")
        .select("*")
        .eq("id", id)
        .single();

      if (propError || !propData) {
        setLoading(false);
        return;
      }

      setProperty(propData);

      if (propData.owner_id) {
        const { data: userData } = await supabase
          .from("profiles")
          .select("full_name, avatar_url, role, verification_tier")
          .eq("id", propData.owner_id)
          .single();
        setOwner(userData);
      }

      setLoading(false);
    }

    fetchListing();
  }, [id]);

  // --- 🆕 THE WIRETAP: CAPTURE LEADS ---
  const captureLead = async (type: "whatsapp" | "call" | "share") => {
    if (!property) return;

    // 1. Google Analytics (The Trend)
    trackEvent(
      "Lead Conversion",
      type === "whatsapp"
        ? "Click WhatsApp"
        : type === "call"
        ? "Click Call"
        : "Share",
      `Property ID: ${property.id}`
    );

    // 2. Supabase Database (The Record)
    // We fire and forget - don't wait for it to finish so UI doesn't lag
    supabase
      .from("leads")
      .insert({
        property_id: property.id,
        type: type,
        meta: {
          page_url: window.location.href,
          referrer: document.referrer,
        },
      })
      .then(({ error }) => {
        if (error) console.error("Lead capture failed:", error);
      });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center text-emerald-500">
        <Loader2 size={32} className="animate-spin mb-4" />
        <p className="font-mono text-xs uppercase tracking-[0.2em]">
          Retrieving Asset Data...
        </p>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center text-white">
        <h1 className="text-2xl font-bold mb-2">Asset Not Found</h1>
        <p className="text-gray-500 mb-6">
          This property listing may have been removed or is restricted.
        </p>
        <Link
          to="/"
          className="px-6 py-3 bg-emerald-600 rounded-lg font-bold text-sm uppercase tracking-wider hover:bg-emerald-500 transition-colors"
        >
          Return to Map
        </Link>
      </div>
    );
  }

  const price =
    property.currency === "USD"
      ? `$${property.price.toLocaleString()}`
      : `₵${property.price.toLocaleString()}`;

  const image =
    property.cover_image_url ||
    property.image_urls?.[0] ||
    "https://images.unsplash.com/photo-1600596542815-e3289047458b";

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-emerald-500 selection:text-black">
      {/* NAVIGATION */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex justify-between items-center p-4 md:p-6 bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
        <Link
          to="/"
          className="pointer-events-auto flex items-center gap-2 px-4 py-2 bg-black/40 backdrop-blur-md border border-white/10 rounded-full hover:bg-white/10 transition-colors group"
        >
          <ArrowLeft
            size={16}
            className="text-gray-400 group-hover:text-white transition-colors"
          />
          <span className="text-xs font-bold uppercase tracking-wider hidden sm:inline">
            Back to Map
          </span>
        </Link>

        <button
          onClick={() => {
            navigator.clipboard.writeText(window.location.href);
            captureLead("share"); // 👈 Log Share
            alert("Link copied to clipboard!");
          }}
          className="pointer-events-auto p-3 bg-black/40 backdrop-blur-md border border-white/10 rounded-full hover:bg-white/10 text-white transition-colors"
        >
          <Share2 size={18} />
        </button>
      </nav>

      {/* HERO IMAGE */}
      <div className="relative h-[60vh] md:h-[70vh] w-full overflow-hidden">
        <img
          src={image}
          alt={property.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/20 to-transparent" />

        <div className="absolute bottom-0 left-0 w-full p-6 md:p-12 max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <span className="inline-block px-3 py-1 mb-4 text-[10px] font-bold uppercase tracking-[0.2em] bg-emerald-500 text-black rounded-sm">
              {property.type === "rent" ? "For Rent" : "For Sale"}
            </span>
            <h1 className="text-3xl md:text-5xl lg:text-6xl font-black tracking-tight leading-tight mb-4 text-white">
              {property.title}
            </h1>
            <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-8 text-gray-300 font-mono text-sm md:text-base">
              <span className="flex items-center gap-2">
                <MapPin size={18} className="text-emerald-500" />
                {property.location_name}
              </span>
              <span className="text-2xl md:text-3xl font-bold text-white font-sans">
                {price}
              </span>
            </div>
          </motion.div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="max-w-5xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-12">
        {/* LEFT COLUMN: DETAILS */}
        <div className="space-y-12">
          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4 border-y border-white/10 py-8">
            <div className="flex flex-col items-center justify-center p-4 bg-white/5 rounded-lg border border-white/5">
              <Bed size={24} className="text-emerald-500 mb-2" />
              <span className="text-2xl font-bold">
                {property.details?.bedrooms || "-"}
              </span>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest">
                Bedrooms
              </span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 bg-white/5 rounded-lg border border-white/5">
              <Bath size={24} className="text-emerald-500 mb-2" />
              <span className="text-2xl font-bold">
                {property.details?.bathrooms || "-"}
              </span>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest">
                Bathrooms
              </span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 bg-white/5 rounded-lg border border-white/5">
              <Square size={24} className="text-emerald-500 mb-2" />
              <span className="text-2xl font-bold">
                {property.details?.sqft || "-"}
              </span>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest">
                Sq Ft
              </span>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">
              About this Property
            </h3>
            <p className="text-lg text-gray-300 leading-relaxed whitespace-pre-wrap">
              {property.description_enriched || property.description}
            </p>
          </div>

          {/* Features */}
          {property.features && property.features.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">
                Amenities
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-y-3 gap-x-4">
                {property.features.map((feat: string, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-gray-300"
                  >
                    <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                    <span className="text-sm">{feat}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: AGENT CARD (Sticky) */}
        <div className="lg:sticky lg:top-8 h-fit space-y-6">
          <div className="bg-[#111] border border-white/10 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-white/10 rounded-full overflow-hidden border-2 border-emerald-500/20">
                {owner?.avatar_url ? (
                  <img
                    src={owner.avatar_url}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-emerald-900/20 text-emerald-500 text-xl font-bold">
                    {owner?.full_name?.[0] || "A"}
                  </div>
                )}
              </div>
              <div>
                <h3 className="font-bold text-lg text-white">
                  {owner?.full_name || "Asta Agent"}
                </h3>
                <div className="flex items-center gap-2 text-xs text-emerald-400 font-mono mt-1">
                  <ShieldCheck size={12} />
                  <span>
                    VERIFIED {owner?.role === "agent" ? "PARTNER" : "SOURCE"}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => {
                  captureLead("whatsapp"); // 👈 Log WhatsApp
                  window.open(
                    `https://wa.me/${property.contact_phone?.replace(
                      /\+/g,
                      ""
                    )}?text=I'm interested in ${property.title}`,
                    "_blank"
                  );
                }}
                className="w-full py-4 bg-[#25D366] hover:bg-[#1ebd59] text-black font-bold rounded-xl flex items-center justify-center gap-2 transition-transform active:scale-95"
              >
                <MessageCircle size={20} />
                Chat on WhatsApp
              </button>
              <button
                onClick={() => {
                  captureLead("call"); // 👈 Log Call
                  window.location.href = `tel:${property.contact_phone}`;
                }}
                className="w-full py-4 bg-white/5 hover:bg-white/10 text-white font-bold rounded-xl flex items-center justify-center gap-2 border border-white/10 transition-colors"
              >
                <Phone size={20} />
                Call Agent
              </button>
            </div>

            <p className="text-[10px] text-gray-500 text-center mt-6 leading-relaxed">
              Protected by{" "}
              <span className="text-emerald-500 font-bold">Asta Verify™</span>.
              <br />
              Never send money before viewing.
            </p>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <footer className="border-t border-white/5 mt-20 py-12 bg-black text-center">
        <Link
          to="/"
          className="inline-flex items-center gap-2 opacity-50 hover:opacity-100 transition-opacity"
        >
          <img src="/logo.png" alt="Asta" className="h-6 w-auto grayscale" />
          <span className="font-bold text-white tracking-widest text-sm">
            ASTA REAL ESTATE
          </span>
        </Link>
      </footer>
    </div>
  );
}
