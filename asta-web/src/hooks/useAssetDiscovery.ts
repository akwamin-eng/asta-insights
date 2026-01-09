import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export function useAssetDiscovery(userPhone: string | null | undefined, userId: string | null | undefined) {
  const [discoveredCount, setDiscoveredCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userPhone || !userId) return;
    checkForLooseAssets();
  }, [userPhone, userId]);

  async function checkForLooseAssets() {
    try {
      // Clean the phone number format if necessary (remove spaces, etc)
      const cleanPhone = userPhone?.replace(/\s+/g, '') || '';

      // Find properties with matching phone but NO owner (or owned by bot)
      // Note: In a real app, strict phone normalization is crucial.
      const { data, error } = await supabase
        .from('properties')
        .select('id')
        .eq('contact_phone', cleanPhone)
        .is('owner_id', null); // currently unowned

      if (error) throw error;
      setDiscoveredCount(data?.length || 0);
    } catch (err: any) {
      console.error('Discovery Scan Failed:', err.message);
    }
  }

  async function claimAssets() {
    if (!userPhone || !userId) return;
    setIsSyncing(true);
    setError(null);

    try {
      const cleanPhone = userPhone.replace(/\s+/g, '');

      const { error } = await supabase
        .from('properties')
        .update({ owner_id: userId, source: 'web_claimed' })
        .eq('contact_phone', cleanPhone)
        .is('owner_id', null);

      if (error) throw error;
      
      // Reset count after successful claim
      setDiscoveredCount(0);
      return true;
    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setIsSyncing(false);
    }
  }

  return { discoveredCount, claimAssets, isSyncing, error };
}
