import React, { useState, useRef, useEffect } from "react";

import { motion } from "framer-motion";

import {
  X,
  Upload,
  MapPin,
  Camera,
  CheckCircle2,
  Loader2,
  Edit,
  Building,
  Map as MapIcon,
  ShieldAlert,
  FileText,
  Scroll,
  Info,
  Wifi,
  Zap,
  Droplets,
  Wind,
  Mountain,
} from "lucide-react";

import { supabase } from "../../lib/supabase";

import LandPlotter from "../LandPlotter";

import GlobalPhoneInput from "../ui/GlobalPhoneInput";

const InfoTooltip = ({ text }: { text: string }) => (
  <div className="group relative inline-flex items-center ml-1.5 cursor-help">
    <Info
      size={12}
      className="text-gray-500 hover:text-emerald-400 transition-colors"
    />

    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-black/95 border border-white/10 rounded-lg text-[10px] text-gray-300 leading-snug opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 text-center shadow-xl">
      {text}

      <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-black/95" />
    </div>
  </div>
);

interface SubmitIntelProps {
  location?: { lat: number; long: number; name?: string };

  currentZoom?: number;

  editingAsset?: any;

  onClose: () => void;

  onSuccess: () => void;
}

export default function SubmitIntelModal({
  location,

  currentZoom,

  editingAsset,

  onClose,

  onSuccess,
}: SubmitIntelProps) {
  const [step, setStep] = useState<
    "type_select" | "plot_land" | "details" | "conflict_check"
  >("type_select");

  const [assetType, setAssetType] = useState<"building" | "land">(
    editingAsset?.property_class === "Land" ? "land" : "building"
  );

  const [uploading, setUploading] = useState(false);

  const [checkingConflict, setCheckingConflict] = useState(false);

  const [conflicts, setConflicts] = useState<any[]>([]);

  const [landPolygon, setLandPolygon] = useState<any>(null);

  const [landMetrics, setLandMetrics] = useState({ acres: 0, sqft: 0 });

  const activeLocation = editingAsset
    ? {
        lat: editingAsset.lat,

        long: editingAsset.long,

        name: editingAsset.location_name,
      }
    : location;

  if (!activeLocation && !editingAsset) return null;

  const [formData, setFormData] = useState({
    title: "",

    price: "",

    currency: "GHS",

    listing_type: "rent",

    description: "",

    location_hint: activeLocation?.name || "",

    contact_phone: "+233",

    // Structure Fields

    bedrooms: "",

    bathrooms: "",

    sqft: "",

    furnishing: "unfurnished",

    amenities: [] as string[],

    // Land Fields

    land_title_status: "indenture",

    zoning: "residential",

    topography: "flat", // New Schema Field

    documents_ready: false,
  });

  const [files, setFiles] = useState<File[]>([]);

  const [previews, setPreviews] = useState<string[]>([]);

  const [existingImages, setExistingImages] = useState<string[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingAsset) {
      setStep("details");

      setFormData({
        title: editingAsset.title || "",

        price: editingAsset.price?.toString() || "",

        currency: editingAsset.currency || "GHS",

        listing_type: editingAsset.type || "rent",

        description: editingAsset.description || "",

        location_hint: editingAsset.location_name || "",

        contact_phone: editingAsset.contact_phone || "+233",

        bedrooms: editingAsset.details?.bedrooms?.toString() || "",

        bathrooms: editingAsset.details?.bathrooms?.toString() || "",

        sqft: editingAsset.details?.sqft?.toString() || "",

        furnishing: editingAsset.details?.furnishing || "unfurnished",

        amenities: editingAsset.features || [],

        land_title_status:
          editingAsset.land_metadata?.title_type || "indenture",

        zoning: editingAsset.land_metadata?.zoning || "residential",

        topography: editingAsset.land_metadata?.topography || "flat",

        documents_ready: editingAsset.land_metadata?.documents_ready || false,
      });

      if (editingAsset.image_urls) setExistingImages(editingAsset.image_urls);
    }
  }, [editingAsset]);

  const handleTypeSelect = (type: "building" | "land") => {
    setAssetType(type);

    if (type === "land") {
      setFormData((prev) => ({ ...prev, listing_type: "sale" }));

      setStep("plot_land");
    } else {
      setStep("details");
    }
  };

  const handleLandPlotComplete = (data: any) => {
    setLandPolygon(data.polygon);

    setLandMetrics({ acres: data.stats.acres, sqft: data.stats.acres * 43560 });

    setFormData((prev) => ({
      ...prev,

      title: `${data.stats.acres.toFixed(2)} Acre Land at ${
        activeLocation?.name || "Unknown Location"
      }`,

      sqft: (data.stats.acres * 43560).toFixed(0),
    }));

    setStep("details");
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);

      setFiles((prev) => [...prev, ...newFiles]);

      const newPreviews = newFiles.map((f) => URL.createObjectURL(f));

      setPreviews((prev) => [...prev, ...newPreviews]);
    }
  };

  const toggleAmenity = (amenity: string) => {
    setFormData((prev) => ({
      ...prev,

      amenities: prev.amenities.includes(amenity)
        ? prev.amenities.filter((a) => a !== amenity)
        : [...prev.amenities, amenity],
    }));
  };

  const initiateSubmission = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!formData.price) return alert("Please enter a price.");

    if (assetType === "land" && landPolygon) {
      setCheckingConflict(true);

      try {
        // RPC call to checking function we created in SQL

        const { data, error } = await supabase.rpc("check_land_overlap", {
          new_geom: landPolygon.geometry,
        });

        if (!error && data && data.length > 0) {
          setConflicts(data);

          setStep("conflict_check");

          setCheckingConflict(false);

          return;
        }
      } catch (err) {
        console.error("Conflict Check Failed:", err);
      }

      setCheckingConflict(false);
    }

    executeUpload();
  };

  const executeUpload = async () => {
    setUploading(true);

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) throw new Error("Authentication required.");

      const newFileUrls: string[] = [];

      if (files.length > 0) {
        for (const file of files) {
          const fileExt = file.name.split(".").pop();

          const fileName = `${user.id}/${Date.now()}-${Math.random()

            .toString(36)

            .substring(7)}.${fileExt}`;

          const { error: uploadError } = await supabase.storage

            .from("properties")

            .upload(fileName, file);

          if (!uploadError) {
            const { data: publicData } = supabase.storage

              .from("properties")

              .getPublicUrl(fileName);

            newFileUrls.push(publicData.publicUrl);
          }
        }
      }

      const finalImageUrls = [...existingImages, ...newFileUrls];

      const payload: any = {
        title: formData.title,

        price: parseFloat(formData.price.replace(/,/g, "")),

        currency: formData.currency,

        type: assetType === "land" ? "sale" : formData.listing_type,

        description: formData.description,

        location_name: formData.location_hint,

        lat: activeLocation?.lat,

        long: activeLocation?.long,

        status: conflicts.length > 0 ? "pending_review" : "active",

        image_urls: finalImageUrls,

        cover_image_url: finalImageUrls[0] || null,

        contact_phone: formData.contact_phone,

        property_class: assetType === "land" ? "Land" : "Residential",

        features: formData.amenities, // Maps to text[] column

        updated_at: new Date().toISOString(),
      };

      if (assetType === "building") {
        payload.details = {
          bedrooms: parseInt(formData.bedrooms || "0"),

          bathrooms: parseInt(formData.bathrooms || "0"),

          sqft: parseInt(formData.sqft || "0"),

          furnishing: formData.furnishing,
        };
      } else {
        if (landPolygon) {
          payload.boundary_geom = landPolygon.geometry; // Maps to PostGIS Geometry

          payload.land_metadata = {
            acres: landMetrics.acres,

            zoning: formData.zoning,

            title_type: formData.land_title_status,

            topography: formData.topography,

            documents_ready: formData.documents_ready,

            conflict_log: conflicts,
          };

          payload.details = { sqft: landMetrics.sqft }; // Keep sqft for searching
        }
      }

      let targetPropertyId = editingAsset?.id;

      if (editingAsset) {
        const { error } = await supabase

          .from("properties")

          .update(payload)

          .eq("id", editingAsset.id);

        if (error) throw error;
      } else {
        // 🟢 FIX: Capture ID of new insertion for Ticket Logic

        const { data: newProp, error } = await supabase

          .from("properties")

          .insert({
            ...payload,

            owner_id: user.id,

            source: "manual_entry",

            location_accuracy: "high",
          })

          .select()

          .single();

        if (error) throw error;

        targetPropertyId = newProp.id;
      }

      // 🟢 INTELLIGENT ROUTING: Create Admin Ticket if Conflict Exists

      if (conflicts.length > 0 && targetPropertyId) {
        await supabase.from("admin_tickets").insert({
          ticket_type: "land_conflict",

          priority: "high",

          status: "open",

          property_id: targetPropertyId,

          owner_id: user.id,

          conflict_details: {
            reason: "Geospatial Overlap Detected",

            overlap_count: conflicts.length,

            conflicting_ids: conflicts.map((c: any) => c.id),
          },
        });
      }

      setTimeout(() => {
        setUploading(false);

        onSuccess();

        onClose();
      }, 500);
    } catch (error: any) {
      console.error("Submission Error", error);

      alert(`Error: ${error.message}`);

      setUploading(false);
    }
  };

  // 🟢 UX FIX: pointer-events-none allows interacting with map behind the modal overlay

  if (step === "plot_land") {
    return (
      <div className="fixed inset-0 z-[100] pointer-events-none">
        <LandPlotter
          onComplete={handleLandPlotComplete}
          onCancel={() => setStep("type_select")}
        />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-lg bg-[#111] border border-white/10 rounded-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5">
          <h3 className="text-white font-bold flex items-center gap-2">
            {step === "type_select" ? (
              <Camera size={18} className="text-emerald-500" />
            ) : (
              <Edit size={18} className="text-purple-500" />
            )}

            {step === "conflict_check"
              ? "Conflict Detected"
              : step === "type_select"
              ? "New Deployment"
              : "Asset Details"}
          </h3>

          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar space-y-6">
          {step === "type_select" && (
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => handleTypeSelect("building")}
                className="p-6 bg-black border border-white/10 rounded-xl hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all text-center flex flex-col items-center gap-3 group"
              >
                <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-emerald-500/20 group-hover:text-emerald-500 transition-colors">
                  <Building size={28} />
                </div>

                <div>
                  <h4 className="text-white font-bold">Structure</h4>

                  <p className="text-[10px] text-gray-500 mt-1">
                    House, Apartment
                  </p>
                </div>
              </button>

              <button
                onClick={() => handleTypeSelect("land")}
                className="p-6 bg-black border border-white/10 rounded-xl hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all text-center flex flex-col items-center gap-3 group"
              >
                <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-emerald-500/20 group-hover:text-emerald-500 transition-colors">
                  <MapIcon size={28} />
                </div>

                <div>
                  <h4 className="text-white font-bold">Land Parcel</h4>

                  <p className="text-[10px] text-gray-500 mt-1">
                    Vacant Lot, Farmland
                  </p>
                </div>
              </button>
            </div>
          )}

          {step === "details" && (
            <>
              {assetType === "land" && landMetrics.acres > 0 && (
                <div className="bg-emerald-900/20 border border-emerald-500/30 p-3 rounded-lg flex items-center gap-3 mb-4">
                  <CheckCircle2 size={20} className="text-emerald-500" />

                  <div>
                    <p className="text-xs text-emerald-400 font-bold uppercase">
                      Boundary Secured
                    </p>

                    <p className="text-[10px] text-gray-400">
                      {landMetrics.acres.toFixed(3)} Acres mapped.
                    </p>
                  </div>

                  <button
                    onClick={() => setStep("plot_land")}
                    className="ml-auto text-[10px] underline text-gray-400 hover:text-white"
                  >
                    Redraw
                  </button>
                </div>
              )}

              <div>
                <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                  Listing Title
                </label>

                <input
                  className="w-full bg-black border border-white/10 rounded-lg p-2.5 text-white text-sm"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  placeholder={
                    assetType === "land"
                      ? "e.g. 2 Plots at East Legon"
                      : "e.g. 3 Bed House"
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {assetType === "building" && (
                  <div>
                    <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                      Listing Type
                    </label>

                    <div className="flex bg-black border border-white/10 rounded-lg p-1">
                      {["rent", "sale"].map((type) => (
                        <button
                          key={type}
                          onClick={() =>
                            setFormData({ ...formData, listing_type: type })
                          }
                          className={`flex-1 py-2 text-xs font-bold uppercase rounded ${
                            formData.listing_type === type
                              ? "bg-emerald-600 text-white"
                              : "text-gray-500"
                          }`}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className={assetType === "land" ? "col-span-2" : ""}>
                  <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                    Valuation ({formData.currency})
                  </label>

                  <div className="relative">
                    <select
                      value={formData.currency}
                      onChange={(e) =>
                        setFormData({ ...formData, currency: e.target.value })
                      }
                      className="absolute left-1 top-1 bottom-1 w-12 bg-white/5 border-none text-xs text-white rounded font-bold"
                    >
                      <option value="GHS">GHS</option>

                      <option value="USD">USD</option>
                    </select>

                    <input
                      type="number"
                      className="w-full bg-black border border-white/10 rounded-lg py-2.5 pl-16 pr-4 text-white text-sm font-mono"
                      value={formData.price}
                      onChange={(e) =>
                        setFormData({ ...formData, price: e.target.value })
                      }
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>

              {/* LAND SPECIFIC FIELDS */}

              {assetType === "land" && (
                <div className="bg-white/5 border border-white/5 rounded-xl p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                        Title Type
                      </label>

                      <select
                        value={formData.land_title_status}
                        onChange={(e) =>
                          setFormData({
                            ...formData,

                            land_title_status: e.target.value,
                          })
                        }
                        className="w-full bg-black border border-white/10 rounded-lg p-2 text-white text-xs outline-none"
                      >
                        <option value="indenture">Indenture</option>

                        <option value="registered">Land Title</option>

                        <option value="vesting_assent">Vesting Assent</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                        Zoning
                      </label>

                      <select
                        value={formData.zoning}
                        onChange={(e) =>
                          setFormData({ ...formData, zoning: e.target.value })
                        }
                        className="w-full bg-black border border-white/10 rounded-lg p-2 text-white text-xs outline-none"
                      >
                        <option value="residential">Residential</option>

                        <option value="commercial">Commercial</option>

                        <option value="agricultural">Agricultural</option>

                        <option value="mixed">Mixed Use</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                        Topography
                      </label>

                      <select
                        value={formData.topography}
                        onChange={(e) =>
                          setFormData({
                            ...formData,

                            topography: e.target.value,
                          })
                        }
                        className="w-full bg-black border border-white/10 rounded-lg p-2 text-white text-xs outline-none"
                      >
                        <option value="flat">Flat</option>

                        <option value="sloped">Sloped</option>

                        <option value="waterlogged">
                          Waterlogged / Swampy
                        </option>

                        <option value="rocky">Rocky</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <label className="text-[10px] font-bold text-gray-500 uppercase flex items-center gap-1">
                        <FileText size={12} /> Documents Ready?
                      </label>

                      <InfoTooltip text="Do you have the site plan and indenture scanned and ready for buyer verification?" />
                    </div>

                    <button
                      onClick={() =>
                        setFormData((p) => ({
                          ...p,

                          documents_ready: !p.documents_ready,
                        }))
                      }
                      className={`w-10 h-5 rounded-full flex items-center transition-colors ${
                        formData.documents_ready
                          ? "bg-emerald-600 justify-end"
                          : "bg-gray-700 justify-start"
                      } p-1`}
                    >
                      <motion.div
                        layout
                        className="w-3 h-3 bg-white rounded-full"
                      />
                    </button>
                  </div>
                </div>
              )}

              {/* STRUCTURE SPECIFIC FIELDS */}

              {assetType === "building" && (
                <>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-[10px] font-bold text-gray-500 uppercase mb-1 block">
                        Beds
                      </label>

                      <input
                        type="number"
                        className="w-full bg-black border border-white/10 rounded-lg p-2 text-sm"
                        value={formData.bedrooms}
                        onChange={(e) =>
                          setFormData({ ...formData, bedrooms: e.target.value })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-gray-500 uppercase mb-1 block">
                        Baths
                      </label>

                      <input
                        type="number"
                        className="w-full bg-black border border-white/10 rounded-lg p-2 text-sm"
                        value={formData.bathrooms}
                        onChange={(e) =>
                          setFormData({
                            ...formData,

                            bathrooms: e.target.value,
                          })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-gray-500 uppercase mb-1 block">
                        SqFt
                      </label>

                      <input
                        type="number"
                        className="w-full bg-black border border-white/10 rounded-lg p-2 text-sm"
                        value={formData.sqft}
                        onChange={(e) =>
                          setFormData({ ...formData, sqft: e.target.value })
                        }
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                      Furnishing
                    </label>

                    <div className="flex bg-black border border-white/10 rounded-lg p-1">
                      {["unfurnished", "furnished", "semi-furnished"].map(
                        (f) => (
                          <button
                            key={f}
                            onClick={() =>
                              setFormData({ ...formData, furnishing: f })
                            }
                            className={`flex-1 py-1.5 text-[10px] font-bold uppercase rounded ${
                              formData.furnishing === f
                                ? "bg-white/20 text-white"
                                : "text-gray-600 hover:bg-white/5"
                            }`}
                          >
                            {f}
                          </button>
                        )
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                      Amenities
                    </label>

                    <div className="flex flex-wrap gap-2">
                      {[
                        { id: "pool", label: "Pool", icon: Droplets },

                        { id: "gym", label: "Gym", icon: Zap },

                        { id: "ac", label: "A/C", icon: Wind },

                        { id: "wifi", label: "Fiber", icon: Wifi },

                        { id: "generator", label: "Gen Set", icon: Zap },

                        {
                          id: "security",

                          label: "Security",

                          icon: ShieldAlert,
                        },
                      ].map((item) => {
                        const active = formData.amenities.includes(item.id);

                        return (
                          <button
                            key={item.id}
                            onClick={() => toggleAmenity(item.id)}
                            className={`px-3 py-1.5 rounded-full border text-[10px] font-bold flex items-center gap-1 transition-all ${
                              active
                                ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                                : "bg-black border-white/10 text-gray-500 hover:border-white/30"
                            }`}
                          >
                            <item.icon size={10} /> {item.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}

              <div>
                <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                  Contact Phone
                </label>

                <GlobalPhoneInput
                  value={formData.contact_phone}
                  onChange={(val) =>
                    setFormData({ ...formData, contact_phone: val })
                  }
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-gray-500 uppercase mb-2 block">
                  Description
                </label>

                <textarea
                  className="w-full h-24 bg-black border border-white/10 rounded-lg p-3 text-white text-xs resize-none"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                />
              </div>

              <div
                onClick={() => fileInputRef.current?.click()}
                className="border border-dashed border-white/20 bg-white/5 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer hover:bg-white/10"
              >
                <Upload size={24} className="text-gray-500 mb-2" />

                <span className="text-xs text-gray-400">
                  Click to upload photos
                </span>

                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileSelect}
                />
              </div>

              {(existingImages.length > 0 || previews.length > 0) && (
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                  {existingImages.map((src, i) => (
                    <div
                      key={`exist-${i}`}
                      className="w-16 h-16 rounded overflow-hidden relative"
                    >
                      <img src={src} className="w-full h-full object-cover" />

                      <button
                        onClick={() =>
                          setExistingImages((p) => p.filter((_, x) => x !== i))
                        }
                        className="absolute inset-0 bg-red-900/50 text-white flex items-center justify-center opacity-0 hover:opacity-100"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}

                  {previews.map((src, i) => (
                    <div
                      key={`prev-${i}`}
                      className="w-16 h-16 rounded overflow-hidden relative"
                    >
                      <img src={src} className="w-full h-full object-cover" />

                      <button
                        onClick={() => {
                          setPreviews((p) => p.filter((_, x) => x !== i));

                          setFiles((p) => p.filter((_, x) => x !== i));
                        }}
                        className="absolute inset-0 bg-black/50 text-white flex items-center justify-center opacity-0 hover:opacity-100"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {step === "conflict_check" && (
            <div className="bg-red-900/20 border border-red-500/50 rounded-xl p-6 text-center">
              <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/30">
                <ShieldAlert size={32} className="text-red-500" />
              </div>

              <h3 className="text-white font-bold text-lg mb-2">
                Boundary Conflict Detected
              </h3>

              <p className="text-gray-400 text-sm mb-6">
                Your plotted area overlaps with{" "}
                <strong>{conflicts.length} existing listings</strong>.
                Proceeding will trigger a manual review.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep("details")}
                  className="flex-1 py-3 border border-white/20 rounded-lg text-white text-xs font-bold uppercase"
                >
                  Cancel
                </button>

                <button
                  onClick={() => executeUpload()}
                  className="flex-1 py-3 bg-red-600 rounded-lg text-white text-xs font-bold uppercase"
                >
                  Proceed
                </button>
              </div>
            </div>
          )}
        </div>

        {step === "details" && (
          <div className="p-4 border-t border-white/10 bg-black/40">
            <button
              onClick={initiateSubmission}
              disabled={uploading || checkingConflict}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {uploading || checkingConflict ? (
                <Loader2 className="animate-spin" />
              ) : (
                <>
                  <CheckCircle2 />{" "}
                  {checkingConflict
                    ? "Verifying Coordinates..."
                    : "Deploy Asset"}
                </>
              )}
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
