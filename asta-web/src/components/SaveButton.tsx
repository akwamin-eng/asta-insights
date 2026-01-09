import React, { useState, useEffect } from 'react';
import { Bookmark, Loader2, Check } from 'lucide-react';
import { supabase } from '../lib/supabase';

interface SaveButtonProps {
  propertyId: number; // Ensure this matches your DB type (int8)
  initialState?: boolean;
  className?: string;
}

export default function SaveButton({ propertyId, initialState = false, className = '' }: SaveButtonProps) {
  const [saved, setSaved] = useState(initialState);
  const [loading, setLoading] = useState(false);

  // Check status on mount (Double check if server state differs from initial)
  useEffect(() => {
    checkStatus();
  }, [propertyId]);

  const checkStatus = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { data } = await supabase
      .from('saved_properties')
      .select('id')
      .eq('user_id', user.id)
      .eq('property_id', propertyId)
      .maybeSingle();
    
    if (data) setSaved(true);
  };

  const toggleSave = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Stop click from opening the listing details
    e.preventDefault();
    
    setLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) {
      alert("Scout Login Required: Please sign in to track assets.");
      setLoading(false);
      return;
    }

    if (saved) {
      // Remove from Watchlist
      const { error } = await supabase
        .from('saved_properties')
        .delete()
        .eq('user_id', user.id)
        .eq('property_id', propertyId);
        
      if (!error) setSaved(false);
    } else {
      // Add to Watchlist
      const { error } = await supabase
        .from('saved_properties')
        .insert({
          user_id: user.id,
          property_id: propertyId,
          notes: 'Captured via Interface'
        });
        
      if (!error) setSaved(true);
    }
    setLoading(false);
  };

  return (
    <button 
      onClick={toggleSave}
      disabled={loading}
      className={`
        flex items-center justify-center gap-2 px-3 py-1.5 rounded-md font-bold uppercase text-[10px] tracking-wider transition-all border
        ${saved 
          ? 'bg-emerald-500 text-black border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]' 
          : 'bg-black/40 text-gray-400 border-white/10 hover:border-white hover:text-white'}
        ${className}
      `}
    >
      {loading ? (
        <Loader2 size={12} className="animate-spin" />
      ) : (
        <>
          {saved ? <Check size={12} strokeWidth={3} /> : <Bookmark size={12} />}
          {saved ? "TRACKING" : "WATCH"}
        </>
      )}
    </button>
  );
}
