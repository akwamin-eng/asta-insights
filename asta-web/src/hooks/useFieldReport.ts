import { useState } from 'react';
import { supabase } from '../lib/supabase';
import { useProfile } from './useProfile';

export function useFieldReport() {
  const { profile, refreshProfile } = useProfile();
  const [loading, setLoading] = useState(false);

  const submitReport = async (
    propertyId: string,
    propertyName: string,
    data: {
      status: string;
      condition: number;
      notes: string;
    }
  ) => {
    if (!profile) return { success: false, error: 'No profile' };
    
    setLoading(true);
    try {
      // 1. Submit the Report
      const { error: reportError } = await supabase.from('field_reports').insert({
        user_id: profile.id,
        property_id: propertyId,
        property_name: propertyName,
        status_verified: data.status,
        condition_rating: data.condition,
        notes: data.notes
      });

      if (reportError) throw reportError;

      // 2. Award Reputation Points (RPC call)
      const POINTS_REWARD = 15;
      const { data: newScore, error: scoreError } = await supabase.rpc('increment_reputation', {
        p_user_id: profile.id,
        p_amount: POINTS_REWARD
      });

      if (scoreError) throw scoreError;

      // 3. Refresh Profile locally to update UI immediately
      await refreshProfile();

      return { success: true, earned: POINTS_REWARD, newScore };

    } catch (e: any) {
      console.error('Field Report Failed:', e);
      return { success: false, error: e.message };
    } finally {
      setLoading(false);
    }
  };

  return { submitReport, loading };
}
