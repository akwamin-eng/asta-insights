import { API_BASE_URL } from "../lib/api";
import React, {
  useState,
  useEffect,
  useMemo,
  useRef,
  useCallback,
} from "react";
import Map, { Source, Layer, Marker } from "react-map-gl";
import * as turf from "@turf/turf";
import "mapbox-gl/dist/mapbox-gl.css";
import { useSearchParams } from "react-router-dom";
import {
  Sun, Moon, Globe, Layers, RotateCcw, MapPin, Hash, Search,
  Loader2, Brain, X, Bug, LogIn, LayoutDashboard, Plus, Check,
  BellRing, Crosshair, Shield, HelpCircle, GripVertical, Send
} from "lucide-react";
import { useLiveListings } from "../hooks/useLiveListings";
import { useAuth } from "../hooks/useAuth";
import { useGooglePlaces } from "../hooks/useGooglePlaces";
import { useGoogleAutocomplete } from "../hooks/useGoogleAutocomplete";
import { useGeolocation } from "../hooks/useGeolocation";
import { AnimatePresence, motion } from "framer-motion";
import { supabase } from "../lib/supabase";
import ListingCard from "./ListingCard";
import AuthModal from "./AuthModal";
import PropertyInspector from "./PropertyInspector";
import UnifiedCommandCenter from "./dossier/UnifiedCommandCenter";
import FieldReportModal from "./dossier/FieldReportModal";
import SubmitIntelModal from "../components/dossier/SubmitIntelModal";
import MapOnboarding from "./MapOnboarding";
import { useAstaAlert } from "../context/AstaAlertProvider";
import type { FeatureCollection } from "geojson";
import type { Property } from "../types/schema";
import SeoHead from "../components/SeoHead";

// --- STYLES ---
const boundaryLayer: any = {
  id: "search-boundary",
  type: "line",
  source: "search-boundary",
  paint: {
    "line-color": "#FACC15",
    "line-width": 2,
    "line-dasharray": [2, 2],
    "line-opacity": 0.8,
  },
};

const boundaryFillLayer: any = {
  id: "search-boundary-fill",
  type: "fill",
  source: "search-boundary",
  paint: { "fill-color": "#FACC15", "fill-opacity": 0.1 },
};

const heatmapLayer: any = {
  id: "heatmap",
  type: "heatmap",
  source: "listings",
  maxzoom: 15,
  paint: {
    "heatmap-weight": ["interpolate", ["linear"], ["get", "price"], 0, 0, 500000, 1],
    "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 1, 9, 3],
    "heatmap-color": [
      "interpolate", ["linear"], ["heatmap-density"],
      0, "rgba(33,102,172,0)", 0.2, "rgb(103,169,207)", 0.4, "rgb(209,229,240)",
      0.6, "rgb(253,219,199)", 0.8, "rgb(239,138,98)", 1, "rgb(178,24,43)"
    ],
    "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 2, 9, 20],
    "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 14, 1, 15, 0],
  },
};

const clusterLayer: any = {
  id: "clusters",
  type: "circle",
  source: "listings",
  filter: ["has", "point_count"],
  paint: {
    "circle-color": ["step", ["get", "point_count"], "#51bb7b", 10, "#f1f075", 30, "#f28cb1"],
    "circle-radius": ["step", ["get", "point_count"], 20, 100, 30, 750, 40],
  },
};

const clusterCountLayer: any = {
  id: "cluster-count",
  type: "symbol",
  source: "listings",
  filter: ["has", "point_count"],
  layout: {
    "text-field": "{point_count_abbreviated}",
    "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
    "text-size": 12,
  },
};

const unclusteredPointLayer: any = {
  id: "unclustered-point",
  type: "circle",
  source: "listings",
  filter: ["!", ["has", "point_count"]],
  paint: {
    "circle-color": ["case", ["==", ["get", "status"], "pending_review"], "#f59e0b", "#10b981"],
    "circle-radius": 8,
    "circle-stroke-width": 3,
    "circle-stroke-color": "#ffffff",
  },
};

const priceLabelLayer: any = {
  id: "price-label",
  type: "symbol",
  source: "listings",
  filter: ["!", ["has", "point_count"]],
  layout: {
    "text-field": ["concat", "₵", ["to-string", ["get", "price_formatted"]]],
    "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
    "text-size": 12,
    "text-offset": [0, 1.5],
    "text-anchor": "top",
    "text-allow-overlap": false,
  },
  paint: {
    "text-color": "#ffffff",
    "text-halo-color": "#000000",
    "text-halo-width": 1.5,
  },
};

const GlassButton = ({ onClick, icon: Icon, active = false, color = "default", tooltip }: any) => {
  const baseStyles = "w-10 h-10 rounded-full backdrop-blur-xl border flex items-center justify-center transition-all duration-300 shadow-lg active:scale-90 active:shadow-inner";
  const colorStyles: any = {
    default: active ? "bg-white text-black border-white shadow-[0_0_15px_rgba(255,255,255,0.3)]" : "bg-black/40 text-white border-white/10 hover:bg-white/10 hover:border-white/30",
    red: active ? "bg-red-500 text-white border-red-400 shadow-[0_0_15px_rgba(239,68,68,0.4)]" : "bg-black/40 text-red-400 border-white/10 hover:bg-red-500/10 hover:border-red-500/30",
    purple: active ? "bg-purple-500 text-white border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.4)]" : "bg-black/40 text-purple-400 border-white/10 hover:bg-purple-500/10 hover:border-purple-500/30",
    emerald: active ? "bg-emerald-500 text-white border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]" : "bg-black/40 text-emerald-400 border-white/10 hover:bg-emerald-500/10 hover:border-emerald-500/30",
    blue: active ? "bg-blue-500 text-white border-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.4)]" : "bg-black/40 text-blue-400 border-white/10 hover:bg-blue-500/10 hover:border-blue-500/30",
  };
  return (
    <button onClick={onClick} className={`${baseStyles} ${colorStyles[color]} group relative`} title={tooltip}>
      <Icon size={18} strokeWidth={2.5} />
    </button>
  );
};

interface Suggestion { type: "location" | "feature"; value: string; placeId?: string; }

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
const ENGINE_URL = API_BASE_URL;
const INITIAL_VIEW_STATE = { longitude: -0.187, latitude: 5.6037, zoom: 11 };
const GHANA_BOUNDS: [number, number, number, number] = [-3.5, 4.5, 1.5, 11.5];
const SIDEBAR_WIDTH = 340;
const HANDLE_WIDTH = 24;
const CONTENT_WIDTH = SIDEBAR_WIDTH - HANDLE_WIDTH;

export default function AstaMap() {
  const { listings, refresh: refreshListings } = useLiveListings();
  const { user } = useAuth();
  const { reverseGeocode, searchPlace, getPlaceDetails, loading: googleLoading } = useGooglePlaces();
  const { location: gpsLocation, getCurrentLocation, loading: gpsLoading } = useGeolocation();
  const { predictions: googlePredictions, getPredictions: fetchGooglePredictions, loading: autocompleteLoading } = useGoogleAutocomplete();

  const [searchParams, setSearchParams] = useSearchParams();
  const isProfileOpen = searchParams.get("mode") === "dossier";
  const dossierSection = (searchParams.get("section") as "dashboard" | "hunter" | "assets") || "dashboard";
  const urlListingId = searchParams.get("listing_id");

  const [viewState, setViewState] = useState({ longitude: -0.187, latitude: 5.6037, zoom: 11 });
  const [isSelectingLocation, setIsSelectingLocation] = useState(false);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);

  useEffect(() => {
    const hasSeen = localStorage.getItem("asta_map_tutorial_seen");
    if (!hasSeen && isMapLoaded) {
      const timer = setTimeout(() => setShowTutorial(true), 2000);
      return () => clearTimeout(timer);
    }
  }, [isMapLoaded]);

  const completeTutorial = () => {
    setShowTutorial(false);
    localStorage.setItem("asta_map_tutorial_seen", "true");
  };

  const [hunterPreferences, setHunterPreferences] = useState<{ property_type: string[]; lifestyle_tags: string[]; }>({ property_type: [], lifestyle_tags: [] });

  const openDossier = (section: "dashboard" | "hunter" | "assets") => setSearchParams({ mode: "dossier", section });
  const closeDossier = () => { setSearchParams({}); refreshListings(); if (user) fetchUserPreferences(); };

  useEffect(() => { if (!isProfileOpen) refreshListings(); }, [isProfileOpen]);

  const handleStartTargeting = () => { setSearchParams({}); setIsSelectingLocation(true); };

  const fetchUserPreferences = async () => {
    if (!user) return;
    const { data } = await supabase.from("profiles").select("preferences").eq("id", user.id).single();
    if (data?.preferences) {
      setHunterPreferences({
        property_type: data.preferences.property_type || [],
        lifestyle_tags: data.preferences.lifestyle_tags || [],
      });
    }
  };

  useEffect(() => { fetchUserPreferences(); }, [user]);

  const [isAuthModalOpen, setAuthModalOpen] = useState(false);
  const [selectedListing, setSelectedListing] = useState<Property | null>(null);
  const [verifyingProp, setVerifyingProp] = useState<{ id: string; title: string; } | null>(null);
  const [draftLocation, setDraftLocation] = useState<{ lat: number; long: number; } | null>(null);
  const [submitLocation, setSubmitLocation] = useState<{ lat: number; long: number; name?: string; } | null>(null);

  const [isSidebarHovered, setIsSidebarHovered] = useState(false);
  const [isMobileExpanded, setIsMobileExpanded] = useState(false);
  const [trendingTags, setTrendingTags] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<"all" | "rent" | "sale">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [mapStyle, setMapStyle] = useState("mapbox://styles/mapbox/satellite-streets-v12");
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showTrustRadar, setShowTrustRadar] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackType, setFeedbackType] = useState<"location" | "bug" | "feature">("bug");
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [searchBoundary, setSearchBoundary] = useState<any>(null);
  const [showEmptyState, setShowEmptyState] = useState<{ location: string; type: "gps" | "area" | "atlas" | "hunter"; } | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const mapRef = useRef<any>(null);

  useEffect(() => {
    if (selectedListing && selectedListing.lat && selectedListing.long) {
      mapRef.current?.flyTo({ center: [selectedListing.long, selectedListing.lat], zoom: 16, pitch: 45, duration: 1500 });
    }
  }, [selectedListing]);

  useEffect(() => {
    if (urlListingId && listings.length > 0) {
      const prop = listings.find((l) => l.id.toString() === urlListingId);
      if (prop) setSelectedListing(prop);
    }
  }, [urlListingId, listings]);

  useEffect(() => {
    fetch(`${ENGINE_URL}/api/trends`).then((res) => res.json()).then((data) => { if (data.trending_tags) setTrendingTags(data.trending_tags); }).catch(() => {});
  }, []);

  useEffect(() => {
    if (gpsLocation && mapRef.current) {
      mapRef.current.flyTo({ center: [gpsLocation.lng, gpsLocation.lat], zoom: 15, duration: 2000 });
    }
  }, [gpsLocation]);

  const handleReset = () => {
    setSearchQuery(""); setSuggestions([]); setFilterType("all"); setMinPrice(""); setMaxPrice("");
    setSelectedListing(null); setShowHeatmap(false); setShowTrustRadar(false); setSearchBoundary(null); setShowEmptyState(null); setDraftLocation(null);
    setSearchParams({});
    setViewState(INITIAL_VIEW_STATE);
    mapRef.current?.flyTo({ center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude], zoom: INITIAL_VIEW_STATE.zoom, pitch: 0, bearing: 0, duration: 1500 });
  };

  const handleDashboardReset = () => {
    handleReset();
  };

  const handleManualListing = () => {
    if (!user) { setAuthModalOpen(true); return; }
    const center = mapRef.current?.getCenter();
    if (center) setDraftLocation({ lat: center.lat, long: center.lng });
  };

  const confirmLocation = async () => {
    if (!draftLocation) return;
    const address = await reverseGeocode(draftLocation.lat, draftLocation.long);
    setSubmitLocation({ lat: draftLocation.lat, long: draftLocation.long, name: address || "Unknown Location" });
    setDraftLocation(null);
  };

  const submitFeedback = async () => {
    if (!feedbackText.trim()) return;
    setIsSubmittingFeedback(true);
    const center = mapRef.current?.getCenter(); const zoom = mapRef.current?.getZoom();
    const isCritical = feedbackText.length > 120 || feedbackText.toLowerCase().includes("login") || feedbackText.toLowerCase().includes("broke");
    try {
      const { error } = await supabase.from("bug_reports").insert({
        description: feedbackText, category: feedbackType, priority: isCritical ? "critical" : "normal", user_id: user?.id || null,
        metadata: { url: window.location.href, userAgent: navigator.userAgent, map_context: { center, zoom, last_search: searchQuery } },
      });
      if (!error) { setFeedbackText(""); setShowFeedback(false); alert("Bug Hunter: System anomaly logged. Command notified."); } else throw error;
    } catch (err) { alert("Transmission failed."); } finally { setIsSubmittingFeedback(false); }
  };

  const selectSuggestion = async (item: Suggestion) => {
    setSearchQuery(item.value); setShowSuggestions(false); setIsSearching(true); setShowEmptyState(null); setSearchBoundary(null);
    if (item.type === "feature") {
      const matches = listings.filter((l) => { const feats = l.features ? l.features.join(" ") : ""; return feats.toLowerCase().includes(item.value.toLowerCase()); });
      if (matches.length > 0) {
        const validPoints = matches.filter((m) => m.lat && m.long).map((m) => turf.point([m.long!, m.lat!]));
        if (validPoints.length > 0) {
          const points = turf.featureCollection(validPoints); const bbox = turf.bbox(points);
          mapRef.current?.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], { padding: 100, duration: 2000, maxZoom: 14 });
        }
      } else alert("No properties with that feature.");
      setIsSearching(false); return;
    }
    if (item.placeId) { const details = await getPlaceDetails(item.placeId); handlePlaceResult(details, item.value); return; }
    const place = await searchPlace(item.value); handlePlaceResult(place, item.value);
  };

  const handlePlaceResult = (place: any, queryName: string) => {
    if (place) {
      if (place.viewport) {
        const { northeast, southwest } = place.viewport;
        mapRef.current?.fitBounds([[southwest.lng, southwest.lat], [northeast.lng, northeast.lat]], { padding: 100, duration: 2500 });
        const polygon = turf.bboxPolygon([southwest.lng, southwest.lat, northeast.lng, northeast.lat]);
        setSearchBoundary({ type: "FeatureCollection", features: [polygon] });
        const hasListings = listings.some((l) => l.lat && l.long && l.lat >= southwest.lat && l.lat <= northeast.lat && l.long >= southwest.lng && l.long <= northeast.lng);
        if (!hasListings) setTimeout(() => setShowEmptyState({ location: place.name || queryName, type: "hunter" }), 1500);
      } else if (place.location) { mapRef.current?.flyTo({ center: [place.location.lng, place.location.lat], zoom: 14, duration: 2500 }); }
    } else alert("Asta Intelligence could not locate " + queryName);
    setIsSearching(false);
  };

  const executeSearch = async (query: string) => { const q = query.trim(); if (!q) return; selectSuggestion({ type: "location", value: q }); };

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value; setSearchQuery(val);
    if (val.length < 3) { setSuggestions([]); setShowSuggestions(false); return; }
    const localMatches = Array.from(new Set(listings.map((l) => l.location_name).filter((name): name is string => !!name)))
      .filter((name) => name.toLowerCase().includes(val.toLowerCase())).slice(0, 2).map((l) => ({ type: "location", value: l } as Suggestion));
    fetchGooglePredictions(val); setSuggestions(localMatches); setShowSuggestions(true);
  };

  useEffect(() => {
    if (googlePredictions && googlePredictions.length > 0) {
      const googleSuggestions = googlePredictions.filter((p: any) => p.description.toLowerCase().includes("ghana")).slice(0, 3)
        .map((p: any) => ({ type: "location", value: p.description, placeId: p.place_id } as Suggestion));
      setSuggestions((prev) => { const existing = new Set(prev.map((p) => p.value)); const novel = googleSuggestions.filter((p: any) => !existing.has(p.value)); return [...prev, ...novel]; });
      if (googleSuggestions.length > 0) setShowSuggestions(true);
    }
  }, [googlePredictions]);

  const applyPricePreset = (label: string) => {
    if (label === "Budget") { setMinPrice(""); setMaxPrice("150000"); }
    if (label === "Family") { setMinPrice("150000"); setMaxPrice("500000"); }
    if (label === "Luxury") { setMinPrice("500000"); setMaxPrice(""); }
  };

  const filteredListings = useMemo(() => {
    return listings.filter((l) => {
      if (!l.price || !l.lat || !l.long) return false;
      const isActive = l.status === "active";
      const isMyPending = l.status === "pending_review" && user?.id === l.owner_id;
      if (!isActive && !isMyPending) return false;
      const matchesType = filterType === "all" || l.type === filterType;
      const price = l.price;
      const min = minPrice ? parseFloat(minPrice) : 0; const max = maxPrice ? parseFloat(maxPrice) : Infinity;
      const matchesPrice = price >= min && price <= max;
      let matchesAssetClass = true;
      if (hunterPreferences?.property_type?.length > 0) { matchesAssetClass = hunterPreferences.property_type.some((t) => (l as any).property_class?.toLowerCase().includes(t.toLowerCase())); }
      let matchesLifestyle = true;
      if (hunterPreferences?.lifestyle_tags?.length > 0) {
        const vibes = (l.features || []).join(" ").toLowerCase();
        matchesLifestyle = hunterPreferences.lifestyle_tags.some((tag) => vibes.includes(tag.toLowerCase()));
      }
      let matchesTrust = true; if (showTrustRadar) matchesTrust = l.location_accuracy === "high";
      return matchesType && matchesPrice && matchesTrust && matchesAssetClass && matchesLifestyle;
    });
  }, [listings, filterType, minPrice, maxPrice, showTrustRadar, hunterPreferences, user]);

  const geojsonData: FeatureCollection = useMemo(() => {
    return {
      type: "FeatureCollection",
      features: filteredListings.map((l) => ({
        type: "Feature", properties: { ...l, price_formatted: (l.price / 1000).toFixed(0) + "k", features_string: l.features ? l.features.join(",") : "" },
        geometry: { type: "Point", coordinates: [l.long!, l.lat!] },
      })),
    };
  }, [filteredListings]);

  const onClickMap = (event: any) => {
    if (isSelectingLocation) {
         setDraftLocation({ lat: event.lngLat.lat, long: event.lngLat.lng });
         setIsSelectingLocation(false);
         return;
    }
    const feature = event.features?.[0];
    if (!feature) {
      if (draftLocation) { setDraftLocation(null); return; }
      if (selectedListing) setSelectedListing(null);
      setShowSuggestions(false);
      return;
    }
    if (feature.layer.id === "clusters") {
      const clusterId = feature.properties.cluster_id;
      mapRef.current?.getSource("listings").getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
          if (err) return;
          mapRef.current?.flyTo({ center: feature.geometry.coordinates, zoom: zoom ? zoom + 1 : 14, duration: 1000 });
        });
      return;
    }
    if (feature.layer.id === "unclustered-point" || feature.layer.id === "price-label") {
      const propId = feature.properties.id; const property = listings.find((l) => l.id == propId);
      if (property) setSelectedListing(property);
    }
  };

  const sidebarVariants = {
    desktop: { x: isSidebarHovered ? 0 : -CONTENT_WIDTH, opacity: 1, transition: { type: "spring", stiffness: 400, damping: 40 } },
    mobile: { y: isMobileExpanded ? 0 : "calc(100% - 100px)", opacity: 1, transition: { type: "spring", stiffness: 400, damping: 40 } },
  };

  const handleStyleToggle = () => {
    setMapStyle((current) => current.includes("satellite") ? "mapbox://styles/mapbox/dark-v11" : current.includes("dark") ? "mapbox://styles/mapbox/streets-v12" : "mapbox://styles/mapbox/satellite-streets-v12");
  };

  return (
    <>
      <SeoHead title="Interactive Market Map" description="Browse geospatial real estate data, land boundaries, and property intelligence in Ghana." />
      <div className="relative h-screen w-full bg-asta-deep font-sans overflow-hidden">
        <style>{`.mapboxgl-canvas-container { cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="%2310b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 22h20L12 2z"/><circle cx="12" cy="14" r="2"/></svg>') 16 16, auto !important; } .mapboxgl-canvas-container.mapboxgl-interactive:active { cursor: grabbing !important; }`}</style>

        <AnimatePresence>{showTutorial && <MapOnboarding onComplete={completeTutorial} />}</AnimatePresence>
        <AnimatePresence>{!isMapLoaded && (<motion.div initial={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1 }} className="absolute inset-0 z-[100] bg-[#050505] flex items-center justify-center"><div className="text-center"><Zap size={48} className="text-emerald-500 mx-auto mb-4 animate-pulse" /><h2 className="text-white font-bold tracking-[0.3em] text-sm animate-pulse">SYSTEM INITIALIZING</h2></div></motion.div>)}</AnimatePresence>

        <Map
          ref={mapRef} {...viewState} onMove={(evt) => setViewState(evt.viewState)}
          style={{ width: "100%", height: "100%", touchAction: "none" }} mapStyle={mapStyle} mapboxAccessToken={MAPBOX_TOKEN}
          interactiveLayerIds={["clusters", "unclustered-point", "price-label"]} onClick={onClickMap}
          reuseMaps={true} preserveDrawingBuffer={true} cursor={isSelectingLocation ? "crosshair" : "auto"}
          maxBounds={GHANA_BOUNDS as any} renderWorldCopies={false} onLoad={() => setTimeout(() => setIsMapLoaded(true), 1000)}
          onContextMenu={(e) => { e.preventDefault(); if (user) setDraftLocation({ lat: e.lngLat.lat, long: e.lngLat.lng }); else setAuthModalOpen(true); }}
          maxTileCacheSize={10}
        >
          {searchBoundary && (<Source id="search-boundary" type="geojson" data={searchBoundary}><Layer {...boundaryFillLayer} /><Layer {...boundaryLayer} /></Source>)}
          <Source id="listings" type="geojson" data={geojsonData} cluster={true} clusterMaxZoom={14} clusterRadius={50}>
            {showHeatmap && <Layer {...heatmapLayer} />} {!showHeatmap && <Layer {...clusterLayer} />} {!showHeatmap && <Layer {...clusterCountLayer} />} <Layer {...unclusteredPointLayer} /> <Layer {...priceLabelLayer} />
          </Source>

          <AnimatePresence>
            {isSelectingLocation && (
              <motion.div initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -50, opacity: 0 }} className="absolute top-8 left-0 right-0 z-50 flex justify-center pointer-events-none">
                <div className="bg-emerald-500 text-black px-6 py-3 rounded-full font-black uppercase tracking-widest shadow-[0_0_30px_rgba(16,185,129,0.5)] flex items-center gap-3 animate-pulse">
                  <Crosshair size={20} className="animate-spin-slow" /><span>Targeting Mode Active</span><span className="text-[10px] bg-black text-white px-2 py-1 rounded">Click Map to Set Coordinates</span>
                  <button onClick={() => setIsSelectingLocation(false)} className="pointer-events-auto bg-black/20 hover:bg-black/40 rounded-full p-1"><X size={14} /></button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {draftLocation && (
            <Marker longitude={draftLocation.long} latitude={draftLocation.lat} draggable={true} onDragEnd={(e) => setDraftLocation({ long: e.lngLat.lng, lat: e.lngLat.lat })} anchor="bottom">
              <div className="flex flex-col items-center gap-1 group cursor-grab active:cursor-grabbing">
                <div className="bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/20 text-white shadow-xl mb-1 flex items-center gap-2">
                  <span className="text-[10px] font-bold">Drag to exact spot</span>
                  <button onClick={(e) => { e.stopPropagation(); setDraftLocation(null); }} className="bg-red-600/20 hover:bg-red-600/40 text-red-400 border border-red-500/30 rounded p-1 transition-colors" title="Cancel Listing"><X size={12} /></button>
                  <button onClick={(e) => { e.stopPropagation(); confirmLocation(); }} className="bg-emerald-600 hover:bg-emerald-500 text-white rounded p-1 transition-colors" title="Confirm Location">{googleLoading ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}</button>
                </div>
                <div className="text-emerald-500 drop-shadow-lg filter hover:scale-110 transition-transform"><MapPin size={40} fill="currentColor" strokeWidth={1} /></div>
                <div className="w-2 h-2 rounded-full bg-emerald-500/50 blur-[2px]" />
              </div>
            </Marker>
          )}

          <div className="map-controls-panel absolute top-4 right-4 md:bottom-32 md:top-auto md:right-[10px] flex flex-col gap-4 z-10 items-end">
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleManualListing} className="add-listing-btn group relative w-14 h-14 rounded-full bg-emerald-500/90 backdrop-blur-2xl border border-white/20 shadow-[0_0_40px_rgba(16,185,129,0.4)] flex items-center justify-center text-white overflow-hidden active:shadow-inner">
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rotate-45" />
              <Plus size={28} strokeWidth={3} className="drop-shadow-lg" />
              <div className="absolute right-full mr-4 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-black/80 text-white text-[10px] font-black uppercase tracking-widest rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap backdrop-blur-md border border-white/10 shadow-xl translate-x-2 group-hover:translate-x-0 transform duration-200">List Asset</div>
            </motion.button>

            <div className="flex flex-col gap-2 p-2 rounded-full bg-black/40 backdrop-blur-xl border border-white/10 shadow-2xl">
              <GlassButton onClick={getCurrentLocation} icon={gpsLoading ? Loader2 : Crosshair} color="emerald" active={gpsLoading} tooltip="Locate Me (GPS)" />
              <GlassButton onClick={handleReset} icon={RotateCcw} tooltip="Reset Map View" />
              <GlassButton onClick={handleStyleToggle} icon={mapStyle.includes("satellite") ? Globe : mapStyle.includes("dark") ? Moon : Sun} tooltip="Toggle Map Theme" />
              <div className="w-full h-px bg-white/10 my-0.5" />
              <GlassButton onClick={() => { setShowHeatmap(!showHeatmap); setShowTrustRadar(false); }} icon={Layers} active={showHeatmap} color="purple" tooltip="Price Heatmap" />
              <GlassButton onClick={() => { setShowTrustRadar(!showTrustRadar); setShowHeatmap(false); }} icon={Shield} active={showTrustRadar} color="purple" tooltip="Verified Trust Radar" />
              <div className="w-full h-px bg-white/10 my-0.5" />
              <GlassButton onClick={() => setShowTutorial(true)} icon={HelpCircle} color="blue" tooltip="System Tutorial" />
              <GlassButton onClick={() => setShowFeedback(true)} icon={Bug} color="red" tooltip="Report Bug" />
            </div>
          </div>

          <motion.div onHoverStart={() => setIsSidebarHovered(true)} onHoverEnd={() => setIsSidebarHovered(false)} animate={window.innerWidth < 768 ? sidebarVariants.mobile : sidebarVariants.desktop} variants={sidebarVariants} transition={{ type: "spring", stiffness: 400, damping: 40 }} style={{ width: SIDEBAR_WIDTH }} className="absolute z-20 flex flex-row pointer-events-auto shadow-2xl md:left-0 md:top-0 md:bottom-0 inset-x-0 bottom-0 h-[80vh] md:h-full rounded-t-xl border-t border-white/20 md:rounded-none md:border-t-0 md:border-r">
            <div style={{ width: CONTENT_WIDTH }} className="flex flex-col bg-asta-deep/95 backdrop-blur-md h-full shrink-0 overflow-hidden">
              <div className="md:hidden flex justify-center pt-2 pb-1 cursor-pointer" onClick={() => setIsMobileExpanded(!isMobileExpanded)}><div className="w-12 h-1 bg-white/20 rounded-full mb-1" /></div>
              <div className="p-3 border-b border-white/10">
                <div className="flex items-center gap-3 mb-3">
                  <img src="/logo.png" alt="Asta" className="h-6 w-auto object-contain" onError={(e: any) => (e.target.style.display = "none")} />
                  <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> ASTA</h1>
                  <div className="ml-auto">
                    {user ? (
                      <button onClick={() => openDossier("dashboard")} className="text-[9px] font-bold text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded hover:bg-emerald-500/10 transition-all flex items-center gap-1"><LayoutDashboard size={10} /> DOSSIER</button>
                    ) : (
                      <button onClick={() => setAuthModalOpen(true)} className="text-[9px] font-bold text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded hover:bg-emerald-500/10 transition-all flex items-center gap-1"><LogIn size={10} /> LOG IN</button>
                    )}
                  </div>
                </div>
                <div className="relative mb-3 z-50">
                  <div className="search-bar-container relative">
                    <input type="text" placeholder="Search..." value={searchQuery} onKeyDown={(e) => e.key === "Enter" && executeSearch(searchQuery)} onChange={handleInput} onFocus={() => suggestions.length > 0 && setShowSuggestions(true)} className="w-full bg-black/40 border border-white/10 rounded-lg py-1.5 pl-3 pr-8 text-xs text-white focus:outline-none focus:border-emerald-500/50 transition-all font-mono" />
                    {isSearching || autocompleteLoading ? <Loader2 className="absolute right-3 top-2 text-emerald-500 w-3 h-3 animate-spin" /> : <Search className="absolute right-3 top-2 text-gray-500 w-3 h-3" />}
                  </div>
                  {showSuggestions && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-black/90 border border-white/10 rounded-lg shadow-xl overflow-hidden backdrop-blur-md">
                      {suggestions.map((item, i) => (
                        <div key={i} onClick={() => selectSuggestion(item)} className="flex items-center gap-3 px-3 py-2 hover:bg-white/10 cursor-pointer transition-colors border-b border-white/5 last:border-0">
                          {item.type === "location" ? <MapPin className="w-3 h-3 text-red-400" /> : <Hash className="w-3 h-3 text-emerald-400" />}
                          <span className="text-xs text-gray-200">{item.value}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className={`${!isMobileExpanded && window.innerWidth < 768 ? "hidden" : "block"}`}>
                  <div className="flex flex-wrap gap-1.5 mb-3 max-h-20 overflow-y-auto scrollbar-hide">
                    {trendingTags.map((tag, i) => (<button key={i} onClick={() => executeSearch(tag)} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[9px] text-asta-platinum hover:bg-emerald-500/20 transition-all">#{tag}</button>))}
                  </div>
                  <div className="flex gap-1 p-1 bg-white/5 rounded-lg mb-3">{["all", "sale", "rent"].map((type) => (<button key={type} onClick={() => setFilterType(type as any)} className={`flex-1 py-1 text-[9px] uppercase font-bold tracking-wider rounded transition-all ${filterType === type ? "bg-emerald-500 text-black" : "text-gray-400 hover:bg-white/5"}`}>{type}</button>))}</div>
                  <div className="mb-2">
                    <div className="flex items-center gap-2 mb-2 bg-white/5 p-1 rounded-lg border border-white/10">
                      <input type="number" placeholder="Min ₵" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} className="w-full bg-transparent text-white text-[10px] pl-2 py-1 focus:outline-none placeholder-gray-600" /><span className="text-gray-600 text-[10px]">-</span><input type="number" placeholder="Max ₵" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} className="w-full bg-transparent text-white text-[10px] pl-2 py-1 focus:outline-none placeholder-gray-600" />
                    </div>
                    <div className="flex gap-1">{["Budget", "Family", "Luxury"].map((label) => (<button key={label} onClick={() => applyPricePreset(label)} className="flex-1 py-1 text-[8px] border border-white/10 rounded hover:bg-white/10 text-gray-400 transition-colors uppercase tracking-wide">{label}</button>))}</div>
                  </div>
                  <button onClick={handleDashboardReset} className="w-full mt-1 flex items-center justify-center gap-2 py-1.5 rounded border border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300 hover:border-red-500/50 transition-all text-[9px] uppercase font-bold tracking-widest"><X size={10} /> Clear Filters</button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-3 scrollbar-hide">
                <AnimatePresence>
                  {filteredListings.map((property) => (<ListingCard key={property.id} property={property as any} isSelected={selectedListing?.id === property.id} onClick={() => setSelectedListing(property)} />))}
                </AnimatePresence>
              </div>
            </div>
            <div style={{ width: HANDLE_WIDTH }} className="hidden md:flex h-full items-center justify-center cursor-pointer group bg-asta-deep/90 border-l border-white/5"><GripVertical size={16} className="text-white/20 group-hover:text-emerald-500 transition-colors" /></div>
          </motion.div>

          <AnimatePresence>
            {showFeedback && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="bg-[#1A1A1A] border border-white/10 w-full max-w-md rounded-xl shadow-2xl overflow-hidden">
                  <div className="p-4 border-b border-white/10 flex justify-between items-center bg-red-500/5"><h3 className="text-white font-bold flex items-center gap-2"><Bug className="text-red-500 w-4 h-4" /> Bug Hunter AI</h3><button onClick={() => setShowFeedback(false)} className="text-gray-400 hover:text-white transition-colors"><X size={18} /></button></div>
                  <div className="p-4 space-y-4"><p className="text-[10px] text-gray-500 font-mono uppercase">// describe the system anomaly:</p><div className="flex gap-2">{[{ id: "location", label: "Map Loc" }, { id: "bug", label: "Software" }, { id: "feature", label: "Request" }].map((type) => (<button key={type.id} onClick={() => setFeedbackType(type.id as any)} className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-wider rounded border transition-all ${feedbackType === type.id ? "bg-red-500 text-white border-red-500" : "bg-white/5 text-gray-400 border-white/10 hover:bg-white/10"}`}>{type.label}</button>))}</div><textarea value={feedbackText} onChange={(e) => setFeedbackText(e.target.value)} placeholder="Scanning system for logs..." className="w-full h-32 bg-black border border-white/10 rounded-lg p-3 text-sm text-white placeholder-gray-700 focus:outline-none focus:border-red-500/50 resize-none font-mono" /><button onClick={submitFeedback} disabled={isSubmittingFeedback || !feedbackText} className="w-full bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors uppercase tracking-widest text-xs">{isSubmittingFeedback ? <><Loader2 size={14} className="animate-spin" /> Analyzing...</> : <><Send size={14} /> Transmit Error Log</>}</button></div>
                </motion.div>
              </div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {selectedListing && <PropertyInspector property={selectedListing} onClose={() => { setSelectedListing(null); setSearchParams({}); }} onVerify={() => setVerifyingProp({ id: selectedListing.id.toString(), title: selectedListing.title })} />}
          </AnimatePresence>

          <AnimatePresence>
            {isProfileOpen && <UnifiedCommandCenter onClose={closeDossier} initialSection={dossierSection} onRequestDeploy={handleStartTargeting} />}
          </AnimatePresence>

          <AnimatePresence>
            {showEmptyState && (
              <motion.div initial={{ y: -100, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -100, opacity: 0 }} className="absolute top-8 left-1/2 -translate-x-1/2 z-40 bg-black/90 text-white px-6 py-4 rounded-lg shadow-2xl border border-white/20 flex flex-col items-center gap-2 backdrop-blur-md max-w-sm text-center">
                <div className="flex items-center gap-2 text-emerald-400 font-bold mb-1">{showEmptyState.type === "hunter" ? <BellRing size={20} className="animate-bounce" /> : <Brain size={20} />}<span>{showEmptyState.type === "hunter" ? "ASTA HUNTER" : "ASTA INTELLIGENCE"}</span></div>
                <p className="text-lg font-bold text-white">{showEmptyState.type === "hunter" ? `No assets found in ${showEmptyState.location}` : `Exploring ${showEmptyState.location}`}</p>
                {showEmptyState.type === "hunter" && (<p className="text-[10px] text-gray-400">Our network is dark in this sector. Configure a Hunter Alert to be notified when assets go live.</p>)}
                <div className="flex gap-2 mt-2 w-full"><button onClick={() => { const loc = showEmptyState.location; setShowEmptyState(null); if (user) { setSearchParams({ mode: "dossier", section: "hunter", zone: loc }); } else setAuthModalOpen(true); }} className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold py-2 rounded transition-colors">{showEmptyState.type === "hunter" ? "Activate Hunter Alert" : "Join Waitlist"}</button><button onClick={() => setShowEmptyState(null)} className="px-3 bg-white/10 hover:bg-white/20 text-white text-[10px] font-bold py-2 rounded transition-colors">Dismiss</button></div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {verifyingProp && <FieldReportModal propertyId={verifyingProp.id} propertyTitle={verifyingProp.title} onClose={() => setVerifyingProp(null)} onSuccess={() => {}} />}
          </AnimatePresence>

          <AnimatePresence>
            {submitLocation && (
              <SubmitIntelModal
                location={submitLocation}
                currentZoom={viewState.zoom}
                onClose={() => setSubmitLocation(null)}
                onSuccess={() => {
                  const loc = submitLocation; setSubmitLocation(null); refreshListings();
                  if (mapRef.current) mapRef.current.flyTo({ center: [loc.long, loc.lat], zoom: 16, duration: 2000 });
                }}
              />
            )}
          </AnimatePresence>

          <div className="absolute bottom-6 left-0 right-0 text-center pointer-events-none z-10 hidden md:block"><p className="text-[10px] text-white/40 font-mono tracking-widest uppercase shadow-black drop-shadow-md">Made with <span className="text-red-500">♥</span> for Ghana</p></div>
          <AuthModal isOpen={isAuthModalOpen} onClose={() => setAuthModalOpen(false)} />
        </Map>
      </div>
    </>
  );
}
