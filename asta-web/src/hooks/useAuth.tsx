import { useState, useEffect } from "react";
import { supabase } from "../supabaseClient"; // 👈 FIX: Import the singleton, do not create a new one
import type { User, Session } from "@supabase/supabase-js";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // 1. STANDARD AUTH: Check active session & Listen for changes
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes (sign in, sign out, etc.)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  // 2. WHATSAPP BRIDGE: Magic Link Catcher 🪄
  // Checks for ?token=... in the URL (from WhatsApp) and logs the user in
  useEffect(() => {
    const handleMagicLogin = async () => {
      const params = new URLSearchParams(window.location.search);
      const magicToken = params.get("token");

      // Only run if token exists and we aren't already processing a login
      if (magicToken) {
        console.log("🪄 WhatsApp Magic Token detected. Exchanging...");

        try {
          // A. Clean URL (remove token so it doesn't stay in history)
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname
          );

          // B. Call Edge Function to exchange token for official Session Link
          const { data, error } = await supabase.functions.invoke(
            "exchange-magic-token",
            {
              body: { token: magicToken },
            }
          );

          if (error) throw error;

          // C. Redirect to the official Supabase Login URL
          if (data?.redirectUrl) {
            console.log("✅ Token Valid. Redirecting to Dashboard...");
            window.location.href = data.redirectUrl;
          }
        } catch (err) {
          console.error("❌ Magic Login Failed:", err);
        }
      }
    };

    // Run immediately on mount
    handleMagicLogin();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return { user, session, loading, signOut };
}
