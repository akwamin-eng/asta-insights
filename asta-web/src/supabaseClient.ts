import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase Environment Variables. Check your .env file!');
}

// 🛡️ PRODUCTION-GRADE SINGLETON
// This pattern ensures that during development (HMR), we strictly reuse
// the same instance attached to the global window object.

const globalAny: any = globalThis;

export const supabase =
  globalAny.supabase ||
  createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });

if (process.env.NODE_ENV !== 'production') {
  globalAny.supabase = supabase;
}
