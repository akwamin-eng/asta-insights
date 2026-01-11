import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

// 🟢 SINGLETON PATTERN: Prevents multiple instances during development hot-reloads
const globalForSupabase = globalThis as unknown as { _supabase: any };

export const supabase =
  globalForSupabase._supabase ||
  createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });

// Only save to global in development to preserve HMR state
if (import.meta.env.DEV) {
  globalForSupabase._supabase = supabase;
}
