import React, { useEffect, useState } from "react";
import { supabase } from "../../supabaseClient";
import { useAuth } from "../../hooks/useAuth";
import { useAstaAlert } from "../../components/ui/AstaAlert"; // 👈 Hook
import { PageReveal } from "../../components/ui/PageReveal"; // 👈 Animation Wrapper
import { Save, Building, Mail, Globe, Loader2 } from "lucide-react";

export default function PartnerSettings() {
  const { user } = useAuth();
  const { toast } = useAstaAlert(); // 👈 Init Toast System

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  // Removed local 'message' state, replaced by global toasts

  const [partnerId, setPartnerId] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    slug: "",
    contact_email: "",
  });

  useEffect(() => {
    if (user) fetchPartnerDetails();
  }, [user]);

  async function fetchPartnerDetails() {
    try {
      // 1. Get User's Partner ID
      const { data: profile } = await supabase
        .from("profiles")
        .select("partner_id")
        .eq("id", user?.id)
        .single();

      if (!profile?.partner_id) {
        setLoading(false);
        return;
      }

      setPartnerId(profile.partner_id);

      // 2. Get Partner Data
      const { data: partner } = await supabase
        .from("partners")
        .select("name, slug, contact_email")
        .eq("id", profile.partner_id)
        .single();

      if (partner) {
        setFormData({
          name: partner.name || "",
          slug: partner.slug || "",
          contact_email: partner.contact_email || "",
        });
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
    } finally {
      setLoading(false);
    }
  }

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);

    if (!partnerId) return;

    try {
      const { error } = await supabase
        .from("partners")
        .update({
          name: formData.name,
          slug: formData.slug,
          contact_email: formData.contact_email,
        })
        .eq("id", partnerId);

      if (error) throw error;

      // 🟢 PREMIUM SUCCESS NOTIFICATION
      toast(
        "success",
        "Protocol Updated",
        "Entity configuration synced to secure database."
      );
    } catch (error) {
      // 🔴 PREMIUM ERROR NOTIFICATION
      toast("error", "Update Failed", error.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="p-10 text-emerald-500 font-mono animate-pulse">
        Decrypting Configuration...
      </div>
    );

  // 🟢 WRAPPED IN PAGE REVEAL
  return (
    <PageReveal className="p-6 md:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Protocol Configuration
        </h1>
        <p className="text-xs text-gray-500 font-mono uppercase tracking-widest mt-1">
          Entity Details // Account Management
        </p>
      </div>

      <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden shadow-2xl relative">
        {/* Decorative Grid Background on Card */}
        <div className="absolute inset-0 tactical-grid opacity-20 pointer-events-none" />

        <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center gap-3 relative z-10">
          <Building size={16} className="text-emerald-500" />
          <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider">
            Entity Profile
          </h3>
        </div>

        <div className="p-6 space-y-6 relative z-10">
          <form className="space-y-6" onSubmit={handleSave}>
            {/* Company Name */}
            <div>
              <label className="block text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">
                Organization Identifier
              </label>
              <div className="relative group focus-within:text-emerald-500">
                <Building
                  size={16}
                  className="absolute left-3 top-3 text-gray-600 group-focus-within:text-emerald-500 transition-colors"
                />
                <input
                  type="text"
                  className="w-full bg-[#050505] border border-white/10 rounded-lg py-2.5 pl-10 pr-4 text-gray-200 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 focus:outline-none transition-all placeholder-gray-700"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            {/* Slug (URL) */}
            <div>
              <label className="block text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">
                Public Uplink (Slug)
              </label>
              <div className="relative flex group focus-within:text-blue-500">
                <div className="bg-white/5 border border-white/10 border-r-0 rounded-l-lg px-3 py-2.5 flex items-center gap-2">
                  <Globe size={14} className="text-gray-500" />
                  <span className="text-xs text-gray-500 font-mono">
                    asta.homes/partner/
                  </span>
                </div>
                <input
                  type="text"
                  className="flex-1 bg-[#050505] border border-white/10 rounded-r-lg py-2.5 px-4 text-blue-400 font-mono focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 focus:outline-none transition-all placeholder-gray-800"
                  value={formData.slug}
                  onChange={(e) =>
                    setFormData({ ...formData, slug: e.target.value })
                  }
                  required
                />
              </div>
              <p className="text-[10px] text-gray-600 mt-1">
                Changing this will alter your public profile URL.
              </p>
            </div>

            {/* Email Address */}
            <div>
              <label className="block text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">
                Communcation Uplink
              </label>
              <div className="relative group focus-within:text-emerald-500">
                <Mail
                  size={16}
                  className="absolute left-3 top-3 text-gray-600 group-focus-within:text-emerald-500 transition-colors"
                />
                <input
                  type="email"
                  className="w-full bg-[#050505] border border-white/10 rounded-lg py-2.5 pl-10 pr-4 text-gray-200 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 focus:outline-none transition-all placeholder-gray-700"
                  value={formData.contact_email}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_email: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-4 border-t border-white/5 flex items-center justify-end gap-4">
              <button
                type="button"
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                onClick={() => fetchPartnerDetails()} // Reset form
              >
                Reset
              </button>
              <button
                disabled={saving}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg text-sm font-bold uppercase tracking-wide transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_30px_rgba(16,185,129,0.4)]"
              >
                {saving ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Save size={16} />
                )}
                {saving ? "Saving..." : "Save Protocol"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </PageReveal>
  );
}
