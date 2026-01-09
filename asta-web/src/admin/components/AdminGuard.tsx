import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../../lib/supabase';
import { ShieldAlert, Loader2, Lock } from 'lucide-react';

const ALLOWED_DOMAIN = 'asta.homes';

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    checkAdminAccess();
  }, []);

  async function checkAdminAccess() {
    const { data: { user } } = await supabase.auth.getUser();

    if (!user || !user.email?.endsWith(`@${ALLOWED_DOMAIN}`)) {
      setAuthorized(false);
    } else {
      setAuthorized(true);
    }
    setLoading(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
      </div>
    );
  }

  if (!authorized) {
    return (
      <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center text-center p-4">
        <div className="w-16 h-16 bg-red-900/20 rounded-full flex items-center justify-center mb-4 border border-red-500/20">
          <ShieldAlert className="w-8 h-8 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Restricted Area</h1>
        <p className="text-gray-500 mb-6 max-w-md">
          Access to Asta Tower is restricted to authorized personnel only. 
          Your attempt has been logged.
        </p>
        <button 
          onClick={() => navigate('/')}
          className="px-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white text-sm font-bold uppercase tracking-wider transition-colors"
        >
          Return to Map
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
