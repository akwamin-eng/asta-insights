import { useEffect, useState, useCallback } from "react";
import { supabase } from "../lib/supabase"; // This now uses the simplified singleton
import type {
  UserProfile,
  HunterPreferences,
  WatchlistItem,
} from "../types/asta_types";

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);

  // Default State prevents "undefined" errors in UI
  const [preferences, setPreferences] = useState<HunterPreferences>({
    locations: [],
    budget_max: 500000,
    property_type: [],
    lifestyle_tags: [],
    alerts_enabled: true,
    deal_trigger_percent: 5,
  });

  const [loading, setLoading] = useState(true);

  // LOG 1: Verify the hook is mounting
  useEffect(() => {
    // console.warn("⚠️ HOOK MOUNTED: useProfile is active.");
  }, []);

  const fetchDossier = useCallback(async () => {
    try {
      setLoading(true);

      // LOG 2: Check Session
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        // console.warn("⚠️ NO SESSION: Supabase reports no active user.");
        setLoading(false);
        return;
      }

      // console.warn(`⚠️ SESSION FOUND: User ID is ${session.user.id}`);

      // 1. Fetch Profile
      const { data: profileData, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", session.user.id)
        .maybeSingle();

      if (error) console.error("❌ DB ERROR:", error.message);

      if (profileData) {
        // console.warn("⚠️ DATA RECEIVED: Profile loaded successfully.");
        setProfile(profileData);
        if (profileData.preferences) {
          // Merge DB preferences with defaults to ensure no missing keys
          setPreferences((prev) => ({ ...prev, ...profileData.preferences }));
        }
      } else {
        console.warn("⚠️ DATA EMPTY: Profile row is missing.");
      }

      // 2. Fetch Watchlist
      const { data: savedData } = await supabase
        .from("saved_properties")
        .select("*, property:properties(*)")
        .eq("user_id", session.user.id);

      if (savedData) {
        const formatted = savedData
          .filter((item: any) => item.property)
          .map((item: any) => ({
            id: item.id,
            property_id: item.property.id,
            title: item.property.title,
            location: item.property.location_name,
            current_price: item.property.price,
            original_price: item.property.price,
            image_url: item.property.cover_image_url,
            added_at: item.created_at,
          }));
        setWatchlist(formatted);
      }
    } catch (err) {
      console.error("CRITICAL FAILURE:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDossier();
  }, [fetchDossier]);

  // --- UPDATE LOGIC (PATCHED FOR 400 ERRORS) ---
  const updatePreferences = async (newPrefs: any) => {
    // 1. Optimistic Update (UI)
    const mergedPrefs = { ...preferences, ...newPrefs };
    setPreferences(mergedPrefs);

    if (profile) {
      const tempProfile = { ...profile, ...newPrefs };
      if (newPrefs.hunter_preferences) {
        tempProfile.hunter_preferences = {
          ...profile.hunter_preferences,
          ...newPrefs.hunter_preferences,
        };
      }
      setProfile(tempProfile);
    }

    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) return;

    // 2. Prepare DB Update
    const updates: any = {
      updated_at: new Date().toISOString(),
    };

    // 🛡️ SANITIZATION FIX:
    // We strip 'undefined' values because Supabase JSONB throws 400 if they exist.
    const cleanPrefs = JSON.parse(JSON.stringify(mergedPrefs));

    // Check if we are updating the JSONB 'preferences' column
    // We look for specific keys that belong to the preference object
    const isPreferenceUpdate =
      "locations" in newPrefs ||
      "budget_max" in newPrefs ||
      "deal_trigger_percent" in newPrefs ||
      "property_type" in newPrefs ||
      "lifestyle_tags" in newPrefs;

    if (isPreferenceUpdate) {
      updates.preferences = cleanPrefs;
    }

    // Handle Top-Level Columns for Gamification/Identity explicitly
    if (newPrefs.full_name !== undefined)
      updates.full_name = newPrefs.full_name;
    if (newPrefs.scout_segment !== undefined)
      updates.scout_segment = newPrefs.scout_segment;
    if (newPrefs.avatar_url !== undefined)
      updates.avatar_url = newPrefs.avatar_url;
    if (newPrefs.rank_title !== undefined)
      updates.rank_title = newPrefs.rank_title;
    if (newPrefs.reputation_score !== undefined)
      updates.reputation_score = newPrefs.reputation_score;

    try {
      const { error } = await supabase
        .from("profiles")
        .update(updates)
        .eq("id", user.id);
      if (error) throw error;

      // 3. Sync to get any trigger-based updates (like new badges)
      await fetchDossier();
    } catch (err) {
      console.error("❌ UPDATE FAILED:", err);
      // Optional: Revert optimistic update here if needed
    }
  };

  return {
    profile,
    watchlist,
    preferences,
    loading,
    refreshProfile: fetchDossier,
    updatePreferences,
    removeFromWatchlist: async (id: number) => {
      setWatchlist((prev) => prev.filter((item) => item.id !== id));
      await supabase.from("saved_properties").delete().eq("id", id);
    },
  };
}
