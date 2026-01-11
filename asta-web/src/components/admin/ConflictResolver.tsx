import React, { useEffect, useState } from 'react';
import Map, { Source, Layer } from 'react-map-gl';
import * as turf from '@turf/turf';
import { supabase } from '../../lib/supabase';
import { ShieldAlert, Check, X, Loader2 } from 'lucide-react';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

const newLayerStyle: any = { id: 'new-poly', type: 'fill', paint: { 'fill-color': '#ef4444', 'fill-opacity': 0.5 } };
const existingLayerStyle: any = { id: 'exist-poly', type: 'fill', paint: { 'fill-color': '#10b981', 'fill-opacity': 0.5 } };
const overlapLayerStyle: any = { id: 'overlap', type: 'line', paint: { 'line-color': '#fff', 'line-width': 2, 'line-dasharray': [2, 2] } };

export default function ConflictResolver({ ticketId, propertyId, onResolve }: any) {
  const [newProperty, setNewProperty] = useState<any>(null);
  const [existingProperties, setExistingProperties] = useState<any[]>([]);
  const [stats, setStats] = useState({ overlapAcres: 0, percent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConflictData();
  }, [propertyId]);

  const loadConflictData = async () => {
    setLoading(true);
    const { data: newProp } = await supabase.from('properties').select('*').eq('id', propertyId).single();
    
    if (!newProp?.boundary_geom) { setLoading(false); return; }
    setNewProperty(newProp);

    const { data: conflicts } = await supabase.rpc('check_land_overlap', { new_geom: newProp.boundary_geom });

    if (conflicts && conflicts.length > 0) {
      const conflictIds = conflicts.map((c: any) => c.id);
      const { data: existingProps } = await supabase.from('properties').select('*').in('id', conflictIds);
      setExistingProperties(existingProps || []);

      if (existingProps && existingProps[0]?.boundary_geom) {
        try {
          const poly1 = newProp.boundary_geom;
          const poly2 = existingProps[0].boundary_geom;
          const intersection = turf.intersect(turf.feature(poly1), turf.feature(poly2));
          if (intersection) {
            const area = turf.area(intersection);
            setStats({ overlapAcres: area * 0.000247105, percent: (area / turf.area(turf.feature(poly1))) * 100 });
          }
        } catch (e) { console.error("Math error", e); }
      }
    }
    setLoading(false);
  };

  const handleDecision = async (decision: 'approve' | 'reject') => {
    if (decision === 'approve') {
      await supabase.from('properties').update({ status: 'active' }).eq('id', propertyId);
    } else {
      await supabase.from('properties').update({ status: 'archived' }).eq('id', propertyId);
    }
    await supabase.from('admin_tickets').update({ status: 'resolved', resolved_at: new Date().toISOString() }).eq('id', ticketId);
    onResolve();
  };

  if (loading || !newProperty) return <div className="h-[500px] flex items-center justify-center text-gray-500"><Loader2 className="animate-spin mr-2" /> Loading Context...</div>;

  return (
    <div className="flex flex-col h-[600px] bg-gray-900 rounded-xl border border-white/10 overflow-hidden relative">
      <div className="flex-1 relative">
        <Map
          initialViewState={{ longitude: newProperty.long || 0, latitude: newProperty.lat || 0, zoom: 16 }}
          mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
          mapboxAccessToken={MAPBOX_TOKEN}
        >
          {existingProperties.map(p => (
            <Source key={p.id} type="geojson" data={p.boundary_geom}><Layer {...existingLayerStyle} /></Source>
          ))}
          <Source type="geojson" data={newProperty.boundary_geom}><Layer {...newLayerStyle} /><Layer {...overlapLayerStyle} /></Source>
        </Map>
        <div className="absolute top-4 left-4 bg-black/90 p-4 rounded-lg border border-white/20 text-white max-w-xs shadow-2xl">
          <h3 className="font-bold text-red-400 flex items-center gap-2 mb-2"><ShieldAlert size={16} /> Conflict Detected</h3>
          <div className="text-xs space-y-2 text-gray-300">
            <p>New Listing: <span className="text-white font-bold">{newProperty.title}</span></p>
            <p>Overlaps With: <span className="text-white font-bold">{existingProperties.length} Existing Title(s)</span></p>
            <div className="h-px bg-white/10 my-2" />
            <p className="text-yellow-400 font-bold">Overlap Severity: {stats.percent.toFixed(1)}%</p>
          </div>
        </div>
      </div>
      <div className="p-4 bg-black border-t border-white/10 flex justify-between items-center z-10">
        <div className="text-xs text-gray-500"><p>Ticket ID: {ticketId}</p></div>
        <div className="flex gap-3">
          <button onClick={() => handleDecision('reject')} className="flex items-center gap-2 px-4 py-2 bg-red-900/30 text-red-400 border border-red-900/50 rounded hover:bg-red-900/50 transition-colors uppercase text-xs font-bold"><X size={14} /> Reject</button>
          <button onClick={() => handleDecision('approve')} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-500 transition-colors uppercase text-xs font-bold"><Check size={14} /> Force Approve</button>
        </div>
      </div>
    </div>
  );
}
