import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Layout,
  Mail,
  Loader2,
  Map as MapIcon,
  ChevronLeft,
  Building,
  Eye,
  Trash2,
  MapPin,
  Edit2,
  Crosshair,
  Megaphone,
  LogOut,
  ShieldAlert,
  Bug, // 👈 Required for icon
} from "lucide-react";
import IdentityModule from "./IdentityModule";
import SmartWatchlist from "./SmartWatchlist";
import HunterPreferences from "./HunterPreferences";
import Dashboard from "./Dashboard";
import SecureInbox from "./SecureInbox";
import OnboardingModule from "./OnboardingModule";
import AssetClaimModal from "./AssetClaimModal";
import SubmitIntelModal from "./SubmitIntelModal";
import HypeManModal from "./HypeManModal";
import BugHunterAgent from "./BugHunterAgent"; // 👈 IMPORTED
import { useProfile } from "../../hooks/useProfile";
import { useHunterIntel } from "../../hooks/useHunterIntel";
import { useAssetDiscovery } from "../../hooks/useAssetDiscovery";
import { supabase } from "../../lib/supabase";
import { useNavigate } from "react-router-dom";

interface UCCProps {
  onClose: () => void;
  onRequestDeploy: () => void;
  initialSection?: "dashboard" | "hunter" | "assets";
}

export default function UnifiedCommandCenter({
  onClose,
  onRequestDeploy,
  initialSection = "dashboard",
}: UCCProps) {
  const navigate = useNavigate();
  const {
    profile,
    watchlist,
    preferences,
    loading,
    updatePreferences,
    removeFromWatchlist,
  } = useProfile();

  const {
    messages,
    loading: intelLoading,
    markAsRead,
  } = useHunterIntel(profile);

  const { discoveredCount, claimAssets, isSyncing } = useAssetDiscovery(
    profile?.phone_number,
    profile?.id
  );
  const [ignoreDiscovery, setIgnoreDiscovery] = useState(false);

  // UX STATE
  const [viewMode, setViewMode] = useState<"dashboard" | "comms" | "assets">(
    "dashboard"
  );
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [dashboardVersion, setDashboardVersion] = useState(0);
  const [localReadIds, setLocalReadIds] = useState<string[]>([]);

  // FEEDBACK STATE
  const [showFeedback, setShowFeedback] = useState(false);

  // ASSET MANAGEMENT STATE
  const [myAssets, setMyAssets] = useState<any[]>([]);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [editingAsset, setEditingAsset] = useState<any>(null);

  // MARKETING AI STATE
  const [marketingAsset, setMarketingAsset] = useState<any>(null);

  // 🟢 INTERNAL USER CHECK
  const isInternal = profile?.email?.endsWith("@asta.homes");

  const unreadCount = (messages || []).filter(
    (m) => m.status === "unread" && !localReadIds.includes(m.id)
  ).length;

  const hasUnread = unreadCount > 0;

  useEffect(() => {
    if (initialSection === "assets") setViewMode("assets");
    else if (initialSection === "hunter") {
      setViewMode("dashboard");
    }
  }, [initialSection]);

  useEffect(() => {
    if (viewMode === "assets" && profile) {
      fetchMyAssets();
    }
  }, [viewMode, profile]);

  const fetchMyAssets = async () => {
    setAssetsLoading(true);
    const { data, error } = await supabase
      .from("properties")
      .select("*")
      .eq("owner_id", profile?.id)
      .order("created_at", { ascending: false });

    if (!error && data) {
      setMyAssets(data);
    }
    setAssetsLoading(false);
  };

  const handleDeleteAsset = async (id: number) => {
    if (
      !confirm(
        "Are you sure you want to delete this listing? This cannot be undone."
      )
    )
      return;

    setMyAssets((prev) => prev.filter((a) => a.id !== id));
    const { error } = await supabase.from("properties").delete().eq("id", id);
    if (error) {
      alert("Error deleting asset. Synchronization failed.");
      fetchMyAssets();
    }
  };

  const toggleAssetStatus = async (id: number, currentStatus: string) => {
    const newStatus = currentStatus === "active" ? "draft" : "active";
    setMyAssets((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: newStatus } : a))
    );
    const { error } = await supabase
      .from("properties")
      .update({ status: newStatus })
      .eq("id", id);
    if (error) {
      alert("Status update failed.");
      fetchMyAssets();
    }
  };

  const handleUpdatePreferences = async (newPrefs: any) => {
    await updatePreferences(newPrefs);
    setDashboardVersion((v) => v + 1);
  };

  const handleClaimAssets = async () => {
    await claimAssets();
    setDashboardVersion((v) => v + 1);
  };

  const handleMarkAsRead = async (id: string) => {
    setLocalReadIds((prev) => [...prev, id]);
    await markAsRead(id);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    onClose();
  };

  useEffect(() => {
    if (profile && !loading) {
      const isDefaultName =
        !profile.full_name ||
        profile.full_name === "Lead Scout" ||
        profile.full_name === "Observer";
      const isUnclassified = !profile.scout_segment;

      if (isDefaultName || isUnclassified) {
        setShowOnboarding(true);
      }
    }
  }, [profile, loading]);

  if (loading) {
    return (
      <div className="fixed inset-0 z-[100] bg-black flex flex-col items-center justify-center gap-6">
        <div className="relative">
          <div className="absolute -inset-4 bg-emerald-500/20 blur-xl rounded-full animate-pulse" />
          <img
            src="/logo.png"
            alt="Asta"
            className="w-12 md:w-16 h-auto relative z-10 opacity-90"
          />
        </div>
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="w-5 h-5 text-emerald-500/50 animate-spin" />
          <span className="text-emerald-500/80 font-mono text-[10px] uppercase tracking-[0.3em] animate-pulse">
            System Initializing...
          </span>
        </div>
      </div>
    );
  }

  const widgetHoverEffect =
    "transition-transform duration-300 hover:scale-[1.01] hover:shadow-[0_4px_30px_rgba(16,185,129,0.1)]";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-[#050505]/98 backdrop-blur-3xl flex flex-col overflow-hidden font-sans"
    >
      <style>{`
        .tactical-grid {
          background-size: 40px 40px;
          background-image: linear-gradient(to right, rgba(16, 185, 129, 0.08) 1px, transparent 1px),
                            linear-gradient(to bottom, rgba(16, 185, 129, 0.08) 1px, transparent 1px);
        }
        .scan-line {
          width: 100%;
          height: 100px;
          background: linear-gradient(to bottom, transparent, rgba(16, 185, 129, 0.1), transparent);
          position: absolute;
          left: 0;
          right: 0;
          animation: scan 8s linear infinite;
          z-index: 2;
          pointer-events: none;
        }
        @keyframes scan {
          0% { top: -100px }
          100% { top: 100% }
        }
        @media (max-width: 768px) {
          .tactical-grid { background-size: 20px 20px; }
        }
      `}</style>

      {/* --- MODALS --- */}
      <AnimatePresence>
        {showOnboarding && (
          <OnboardingModule
            currentName={profile?.full_name || ""}
            onComplete={() => {
              setShowOnboarding(false);
              setDashboardVersion((v) => v + 1);
            }}
          />
        )}

        {editingAsset && (
          <SubmitIntelModal
            editingAsset={editingAsset}
            onClose={() => setEditingAsset(null)}
            onSuccess={() => {
              fetchMyAssets();
              setEditingAsset(null);
            }}
          />
        )}

        {marketingAsset && (
          <HypeManModal
            property={marketingAsset}
            onClose={() => setMarketingAsset(null)}
          />
        )}

        {/* 🟢 BUG REPORT AGENT (Restored Premium Modal) */}
        {showFeedback && (
          <BugHunterAgent onClose={() => setShowFeedback(false)} />
        )}
      </AnimatePresence>

      {!ignoreDiscovery && discoveredCount > 0 && (
        <AssetClaimModal
          count={discoveredCount}
          onClaim={handleClaimAssets}
          onIgnore={() => setIgnoreDiscovery(true)}
          isSyncing={isSyncing}
        />
      )}

      {/* HEADER */}
      <header className="h-16 md:h-20 border-b border-white/10 flex items-center justify-between px-4 md:px-8 bg-black/80 md:bg-black/60 shrink-0 z-50 backdrop-blur-md">
        <div className="flex items-center gap-3 md:gap-8 overflow-hidden">
          <div className="flex items-center gap-2 md:gap-4 shrink-0">
            <div className="relative">
              <img
                src="/logo.png"
                alt="Asta"
                className="h-6 md:h-8 w-auto brightness-110"
              />
              <div className="absolute -inset-1 bg-emerald-500/20 blur-md rounded-full -z-10" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-white font-black tracking-[0.1em] text-[10px] md:text-lg uppercase whitespace-nowrap">
                  <span className="md:hidden">Command Intel</span>
                  <span className="hidden md:inline">
                    Unified Command Intelligence
                  </span>
                </h1>
                <span className="hidden md:inline text-[8px] bg-emerald-500/20 text-emerald-500 px-1.5 py-0.5 rounded border border-emerald-500/30 font-mono">
                  v3.8
                </span>
              </div>
              <p className="hidden md:block text-[9px] text-gray-500 font-mono tracking-widest uppercase">
                Level: {profile?.rank_title || "RECRUIT"}
              </p>
            </div>
          </div>

          <div className="flex bg-white/5 rounded-lg p-1 border border-white/10 shrink-0 ml-auto md:ml-0">
            <button
              onClick={() => setViewMode("dashboard")}
              className={`px-3 md:px-4 py-1.5 md:py-2 rounded text-[9px] md:text-[10px] font-bold uppercase tracking-wider transition-all flex items-center gap-1 md:gap-2 ${
                viewMode === "dashboard"
                  ? "bg-emerald-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <Layout size={12} />{" "}
              <span className="hidden sm:inline">Dashboard</span>
            </button>
            <button
              onClick={() => setViewMode("assets")}
              className={`px-3 md:px-4 py-1.5 md:py-2 rounded text-[9px] md:text-[10px] font-bold uppercase tracking-wider transition-all flex items-center gap-1 md:gap-2 ${
                viewMode === "assets"
                  ? "bg-purple-600 text-white shadow-[0_0_15px_rgba(147,51,234,0.4)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <Building size={12} />{" "}
              <span className="hidden sm:inline">Assets</span>
            </button>
            <button
              onClick={() => setViewMode("comms")}
              className={`relative px-3 md:px-4 py-1.5 md:py-2 rounded text-[9px] md:text-[10px] font-bold uppercase tracking-wider transition-all flex items-center gap-1 md:gap-2 ${
                viewMode === "comms"
                  ? "bg-blue-600 text-white shadow-lg"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <Mail size={12} /> <span className="hidden sm:inline">Comms</span>
              {hasUnread && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border border-black animate-pulse" />
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-3 ml-2">
          {/* 🟢 REPORT BUG BUTTON (Restored) */}
          <button
            onClick={() => setShowFeedback(true)}
            className="group relative p-2 md:p-3 bg-red-500/10 hover:bg-red-500/20 rounded-xl text-red-400 hover:text-red-300 transition-all border border-red-500/20 hover:border-red-500/50 shrink-0"
            title="Report Anomaly"
          >
            <Bug size={18} className="md:w-6 md:h-6" />
          </button>

          {/* 🟢 ASTA TOWER SHORTCUT (Internal Only) */}
          {isInternal && (
            <button
              onClick={() => navigate("/admin/dashboard")}
              className="group relative p-2 md:p-3 bg-purple-600/20 hover:bg-purple-600/40 rounded-xl text-purple-400 hover:text-white transition-all border border-purple-500/30 hover:border-purple-500 shrink-0"
              title="Asta Tower Access"
            >
              <ShieldAlert size={18} className="md:w-6 md:h-6" />
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-8 h-[2px] bg-purple-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity animate-pulse"></div>
            </button>
          )}

          {/* LOGOUT BUTTON */}
          <button
            onClick={handleLogout}
            className="p-2 md:p-3 hover:bg-white/10 rounded-xl text-gray-400 hover:text-white transition-all border border-white/5 hover:border-white/20 shrink-0 bg-white/5"
            title="Sign Out"
          >
            <LogOut size={18} className="md:w-6 md:h-6" />
          </button>

          {/* CLOSE BUTTON */}
          <button
            onClick={onClose}
            className="p-2 md:p-3 hover:bg-red-500/10 rounded-xl text-gray-400 hover:text-red-500 transition-all border border-white/5 hover:border-red-500/20 shrink-0 bg-white/5"
          >
            <X size={18} className="md:w-6 md:h-6" />
          </button>
        </div>
      </header>

      {/* ... (Rest of component remains unchanged) ... */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 md:space-y-8 custom-scrollbar bg-black tactical-grid relative pb-32">
        <div className="scan-line" />

        <div className="max-w-[1700px] mx-auto space-y-6 md:space-y-8 relative z-10">
          {/* TOP WIDGETS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
            <div className={`w-full ${widgetHoverEffect}`}>
              <IdentityModule profile={profile} />
            </div>
            <motion.div
              className={`h-auto md:h-full rounded-2xl overflow-hidden ${widgetHoverEffect}`}
              animate={
                initialSection === "hunter"
                  ? {
                      boxShadow: [
                        "0 0 0px rgba(16,185,129,0)",
                        "0 0 25px rgba(16,185,129,0.4)",
                        "0 0 0px rgba(16,185,129,0)",
                      ],
                      borderColor: [
                        "rgba(255,255,255,0.1)",
                        "rgba(16,185,129,1)",
                        "rgba(255,255,255,0.1)",
                      ],
                    }
                  : {}
              }
              transition={{
                duration: 2,
                repeat: initialSection === "hunter" ? Infinity : 0,
              }}
            >
              <HunterPreferences
                preferences={preferences}
                onUpdate={handleUpdatePreferences}
              />
            </motion.div>
            <div className={`w-full h-[350px] md:h-auto ${widgetHoverEffect}`}>
              <SmartWatchlist
                items={watchlist}
                onRemove={removeFromWatchlist}
              />
            </div>
          </div>

          {/* LOWER SECTION */}
          <div className="w-full relative">
            <div className="bg-[#0A0A0A]/60 border border-white/10 rounded-2xl overflow-hidden flex flex-col min-h-[500px] md:min-h-[650px] relative shadow-3xl backdrop-blur-xl">
              {viewMode === "dashboard" && (
                <div className="flex-1 w-full relative z-20">
                  <Dashboard key={dashboardVersion} />
                </div>
              )}
              {viewMode === "comms" && (
                <SecureInbox
                  messages={messages || []}
                  loading={intelLoading}
                  onRead={handleMarkAsRead}
                />
              )}

              {/* ASSETS VIEW */}
              {viewMode === "assets" && (
                <div className="flex flex-col h-full">
                  <div className="p-4 md:p-5 bg-purple-500/5 border-b border-white/10 flex justify-between items-center relative z-20">
                    <span className="text-[9px] md:text-[11px] font-black text-purple-500 uppercase tracking-[0.2em] md:tracking-[0.4em] flex items-center gap-2 md:gap-3">
                      <Building size={14} /> Deployed Assets
                    </span>

                    <button
                      onClick={onRequestDeploy}
                      className="bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/30 px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 transition-all group"
                    >
                      <Crosshair
                        size={12}
                        className="group-hover:rotate-90 transition-transform"
                      />{" "}
                      Target New Location
                    </button>
                  </div>

                  <div className="flex-1 p-6 overflow-y-auto">
                    {assetsLoading ? (
                      <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-3">
                        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
                        <span className="text-xs font-mono uppercase">
                          Retrieving Asset Data...
                        </span>
                      </div>
                    ) : myAssets.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-xl bg-white/[0.02]">
                        <Building className="w-12 h-12 mb-3 opacity-50" />
                        <h3 className="text-white font-bold">
                          No Assets Found
                        </h3>
                        <p className="text-xs max-w-xs text-center mt-1">
                          You have not deployed any listings yet.
                        </p>
                      </div>
                    ) : (
                      <div className="grid gap-3">
                        {myAssets.map((asset) => (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            key={asset.id}
                            className="group bg-black/40 border border-white/10 hover:border-purple-500/50 rounded-lg p-4 transition-all flex items-center gap-4 relative overflow-hidden"
                          >
                            <div
                              className={`absolute left-0 top-0 bottom-0 w-1 ${
                                asset.status === "active"
                                  ? "bg-emerald-500"
                                  : "bg-yellow-500"
                              }`}
                            />
                            <div className="w-16 h-16 bg-white/5 rounded-md overflow-hidden flex-shrink-0 flex items-center justify-center border border-white/5">
                              {asset.image_urls && asset.image_urls[0] ? (
                                <img
                                  src={asset.image_urls[0]}
                                  alt=""
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <Building size={20} className="text-gray-600" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0 pl-2">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="text-white font-bold truncate text-sm">
                                  {asset.title || "Untitled Property"}
                                </h4>
                                <span
                                  className={`text-[9px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${
                                    asset.status === "active"
                                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                      : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                  }`}
                                >
                                  {asset.status}
                                </span>
                              </div>
                              <div className="flex items-center gap-4 text-xs text-gray-500 font-mono">
                                <span className="flex items-center gap-1">
                                  <MapPin size={10} /> {asset.location_name}
                                </span>
                                <span className="text-white">
                                  ₵{asset.price?.toLocaleString()}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-300">
                              <button
                                onClick={() => setMarketingAsset(asset)}
                                className="p-2 hover:bg-blue-500/10 rounded text-gray-400 hover:text-blue-400 transition-colors"
                                title="Generate Marketing Strategy"
                              >
                                <Megaphone size={16} />
                              </button>

                              <button
                                onClick={() => setEditingAsset(asset)}
                                className="p-2 hover:bg-purple-500/10 rounded text-gray-400 hover:text-purple-400 transition-colors"
                                title="Edit Asset"
                              >
                                <Edit2 size={16} />
                              </button>
                              <button
                                onClick={() =>
                                  toggleAssetStatus(asset.id, asset.status)
                                }
                                className="p-2 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors"
                                title={
                                  asset.status === "active"
                                    ? "Set to Draft"
                                    : "Activate"
                                }
                              >
                                {asset.status === "active" ? (
                                  <Eye size={16} />
                                ) : (
                                  <Eye size={16} className="text-yellow-500" />
                                )}
                              </button>
                              <button
                                onClick={() => handleDeleteAsset(asset.id)}
                                className="p-2 hover:bg-red-500/10 rounded text-gray-400 hover:text-red-400 transition-colors"
                                title="Delete Asset"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* BACK TO MAP */}
        <div className="fixed bottom-0 left-0 right-0 p-4 pb-8 md:pb-8 flex justify-center bg-gradient-to-t from-black via-black/90 to-transparent z-[60] pointer-events-none">
          <button
            onClick={onClose}
            className="pointer-events-auto group flex items-center gap-2 md:gap-3 px-8 md:px-10 py-3 md:py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-full font-black text-[10px] md:text-xs uppercase tracking-[0.15em] shadow-[0_10px_40px_rgba(16,185,129,0.4)] transition-all hover:-translate-y-1 active:translate-y-0 border border-emerald-400/50 backdrop-blur-md"
          >
            <ChevronLeft
              size={16}
              className="group-hover:-translate-x-1 transition-transform"
            />
            <span>Return to Map</span>
            <MapIcon size={16} />
          </button>
        </div>
      </main>
    </motion.div>
  );
}
