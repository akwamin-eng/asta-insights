import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Building, Map as MapIcon, Loader2, CheckCircle2 } from "lucide-react";
import { supabase } from "../../lib/supabase"; // 🟢 Changed to match standard lib path
import LandPlotter from "../LandPlotter";

export default function SubmitIntelModal({ location, currentZoom, editingAsset, onClose, onSuccess }: any) {
  const isEditing = !!(editingAsset && editingAsset.id);
  const [step, setStep] = useState(isEditing ? 'details' : 'type_select');
  const [assetType, setAssetType] = useState(editingAsset?.property_class === 'Land' ? 'land' : 'building');
  const [uploading, setUploading] = useState(false);
  const [landMetrics, setLandMetrics] = useState({ acres: 0, sqft: 0 });
  const [landPolygon, setLandPolygon] = useState<any>(null);

  const [formData, setFormData] = useState({
    title: editingAsset?.title || "", 
    price: editingAsset?.price || "", 
    currency: editingAsset?.currency || "GHS", 
    description: editingAsset?.description || ""
  });

  const handleLandComplete = (path: any, stats: any) => {
    setLandPolygon(path);
    setLandMetrics(stats);
    setFormData({ ...formData, title: `${stats.acres.toFixed(2)} Acre Plot` });
    setStep('details');
  };

  const save = async () => {
    setUploading(true);
    try {
      const payload = {
        ...formData,
        property_class: assetType === 'land' ? 'Land' : 'Residential',
        lat: editingAsset?.lat || location?.lat,
        long: editingAsset?.long || location?.long,
        boundary_geom: landPolygon,
        status: 'active'
      };
      const { error } = isEditing 
        ? await supabase.from("properties").update(payload).eq("id", editingAsset.id)
        : await supabase.from("properties").insert([payload]);
      
      if (error) throw error;
      onSuccess(); 
      onClose();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setUploading(false);
    }
  };

  if (step === 'plot_land') return <div className="fixed inset-0 z-[250]"><LandPlotter mode="select" onComplete={handleLandComplete} onCancel={() => setStep('type_select')} /></div>;

  return (
    <div className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-md bg-[#111] border border-white/10 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5">
          <h3 className="font-bold text-white">New Deployment</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={20} /></button>
        </div>
        <div className="p-8">
          {step === 'type_select' ? (
            <div className="grid grid-cols-2 gap-4">
              <button onClick={() => { setAssetType('building'); setStep('details'); }} className="p-6 bg-white/5 border border-white/10 rounded-xl flex flex-col items-center gap-3 hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all group">
                <Building size={40} className="text-gray-400 group-hover:text-emerald-400" />
                <span className="font-bold text-white">Structure</span>
              </button>
              <button onClick={() => { setAssetType('land'); setStep('plot_land'); }} className="p-6 bg-white/5 border border-white/10 rounded-xl flex flex-col items-center gap-3 hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all group">
                <MapIcon size={40} className="text-gray-400 group-hover:text-emerald-400" />
                <span className="font-bold text-white">Land Parcel</span>
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input className="w-full bg-black border border-white/10 rounded-lg p-3 text-white" placeholder="Title" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
              <div className="flex gap-2">
                <input className="flex-1 bg-black border border-white/10 rounded-lg p-3 text-white" placeholder="Price" type="number" value={formData.price} onChange={e => setFormData({...formData, price: e.target.value})} />
                <select className="bg-black border border-white/10 rounded-lg p-3 text-white" value={formData.currency} onChange={e => setFormData({...formData, currency: e.target.value})}><option>GHS</option><option>USD</option></select>
              </div>
              <textarea className="w-full bg-black border border-white/10 rounded-lg p-3 h-24 text-white" placeholder="Description" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
              <button onClick={save} disabled={uploading} className="w-full bg-emerald-600 py-4 rounded-xl font-bold text-white hover:bg-emerald-500 transition-colors">
                {uploading ? <Loader2 className="animate-spin mx-auto" /> : "Deploy Asset"}
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
