import React, { useEffect, useState } from 'react';
import { supabase } from '../../../lib/supabase';
import { Building2, MapPin, Tag } from 'lucide-react';
import MarketingStatus from './MarketingStatus'; // Import the widget

export default function PropertyManager() {
  const [myProperties, setMyProperties] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMyProperties() {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data } = await supabase
        .from('properties')
        .select('*')
        .eq('owner_id', user.id)
        .order('created_at', { ascending: false });

      if (data) setMyProperties(data);
      setLoading(false);
    }
    fetchMyProperties();
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Scanning Grid...</div>;

  return (
    <div className="space-y-6">
      {myProperties.map((prop) => (
        <div key={prop.id} className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
          <div className="p-4 flex gap-4">
            <img src={prop.cover_image_url} className="w-20 h-20 object-cover rounded-lg border border-white/10" />
            <div className="flex-1">
              <h3 className="text-white font-bold text-sm">{prop.title}</h3>
              <div className="flex items-center gap-2 text-gray-400 text-[10px] mt-1">
                <MapPin size={10} /> {prop.location_name}
              </div>
              <div className="mt-2 flex gap-2">
                <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-bold uppercase rounded">
                  {prop.status}
                </span>
              </div>
            </div>
          </div>

          {/* GENTLE UPDATE: Insert the Marketing Status here */}
          <div className="px-4 pb-4">
            <MarketingStatus propertyId={prop.id} />
          </div>
        </div>
      ))}
    </div>
  );
}
