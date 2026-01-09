import React, { useState, useCallback, useMemo } from 'react';
import { GoogleMap, useJsApiLoader, Polygon, Marker } from '@react-google-maps/api';
import { Ruler, Trash2, Undo, Layers, CheckCircle2, X } from 'lucide-react';

const containerStyle = { width: '100%', height: '100%' };
const defaultCenter = { lat: 5.6639, lng: -0.1665 }; 
const libraries: ("geometry" | "drawing" | "places")[] = ["geometry"];

export default function LandPlotter({ mode = 'standalone', initialLocation, initialZoom = 18, onComplete, onCancel }: any) {
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_API_KEY || "",
    libraries: libraries
  });

  const [path, setPath] = useState<{ lat: number; lng: number }[]>([]);
  const [mapTypeId, setMapTypeId] = useState<any>('hybrid');

  const center = useMemo(() => {
    if (initialLocation?.lat) return { lat: initialLocation.lat, lng: initialLocation.long };
    return defaultCenter;
  }, [initialLocation]);

  const stats = useMemo(() => {
    if (path.length < 3 || !window.google) return { acres: 0, plots: 0 };
    const areaSqM = google.maps.geometry.spherical.computeArea(path);
    const areaSqFt = areaSqM * 10.7639;
    return { acres: areaSqFt / 43560, plots: areaSqFt / 7000 };
  }, [path]);

  if (!isLoaded) return <div className="h-full flex items-center justify-center bg-slate-900 text-white">Loading Map...</div>;

  return (
    <div className="flex flex-col h-full bg-slate-900">
      <div className="bg-slate-950 p-3 border-b border-white/10 flex justify-between items-center z-10">
        <h2 className="text-white font-bold text-sm">Land Registry</h2>
        <div className="flex gap-2">
          <button onClick={() => setMapTypeId(mapTypeId === 'hybrid' ? 'roadmap' : 'hybrid')} className="p-2 bg-white/10 rounded"><Layers size={16} /></button>
          <button onClick={() => setPath(p => p.slice(0, -1))} className="p-2 bg-white/10 rounded"><Undo size={16} /></button>
          <button onClick={() => setPath([])} className="p-2 bg-red-500/20 text-red-400 rounded"><Trash2 size={16} /></button>
          {onCancel && <button onClick={onCancel} className="p-2 bg-white/10 rounded"><X size={16} /></button>}
        </div>
      </div>
      <div className="relative flex-1">
        <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={initialZoom} onClick={(e: any) => setPath([...path, { lat: e.latLng.lat(), lng: e.latLng.lng() }])} mapTypeId={mapTypeId} options={{ disableDefaultUI: true, zoomControl: true }}>
          <Polygon paths={path} options={{ fillColor: "#10b981", fillOpacity: 0.3, strokeColor: "#34d399", strokeWeight: 2 }} />
          {path.map((p, i) => <Marker key={i} position={p} label={{ text: (i + 1).toString(), color: "white" }} />)}
        </GoogleMap>
        <div className="absolute bottom-4 left-4 bg-black/80 p-3 rounded-lg border border-white/10">
          <div className="text-xl font-bold text-white">{stats.plots.toFixed(2)} Plots</div>
          <div className="text-xs text-gray-400">{stats.acres.toFixed(3)} Acres</div>
        </div>
        {path.length > 2 && onComplete && (
          <button onClick={() => onComplete(path, stats)} className="absolute bottom-4 right-4 bg-emerald-600 p-3 rounded-lg text-white font-bold flex items-center gap-2">
            <CheckCircle2 size={18} /> Confirm
          </button>
        )}
      </div>
    </div>
  );
}
