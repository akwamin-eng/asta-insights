import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, Siren, Loader2 } from 'lucide-react';

interface IntelligenceCardProps {
  propertyId: number;
  locationName: string;
}

export default function IntelligenceCard({ propertyId, locationName }: IntelligenceCardProps) {
  const [votingStatus, setVotingStatus] = useState<'idle' | 'submitting' | 'voted'>('idle');
  const [voteType, setVoteType] = useState<string | null>(null);

  // 1. UNIQUE DEVICE ID (Simple Fingerprinting)
  const getDeviceId = () => {
    let id = localStorage.getItem('asta_device_id');
    if (!id) {
      id = 'dev_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('asta_device_id', id);
    }
    return id;
  };

  // 2. RESET STATE ON PROPERTY CHANGE
  useEffect(() => {
    const history = JSON.parse(localStorage.getItem('asta_vote_history') || '{}');
    if (history[propertyId]) {
      setVotingStatus('voted');
      setVoteType(history[propertyId]);
    } else {
      setVotingStatus('idle');
      setVoteType(null);
    }
  }, [propertyId]);

  const handleVote = async (type: 'confirmed' | 'sus' | 'scam') => {
    setVotingStatus('submitting');
    
    try {
      // API Call
      const response = await fetch('http://127.0.0.1:8000/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          property_id: propertyId,
          vote_type: type,
          device_id: getDeviceId()
        }),
      });

      if (response.ok) {
        setVotingStatus('voted');
        setVoteType(type);
        
        const history = JSON.parse(localStorage.getItem('asta_vote_history') || '{}');
        history[propertyId] = type;
        localStorage.setItem('asta_vote_history', JSON.stringify(history));
      } else {
        setVotingStatus('idle');
        alert("Vote failed. Please try again.");
      }
    } catch (e) {
      console.error(e);
      setVotingStatus('idle');
    }
  };

  if (votingStatus === 'voted') {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-6 text-center animate-in fade-in zoom-in duration-300">
        <div className="w-12 h-12 bg-emerald-500/20 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-3">
          <ShieldCheck size={24} />
        </div>
        <h3 className="text-white font-bold text-sm">Signal Recorded</h3>
        <p className="text-gray-400 text-xs mt-1">
          Thanks for helping verify {locationName}. <br/>
          Your vote: <span className="text-white font-mono uppercase">{voteType}</span>
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5">
      <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
        <ShieldCheck size={14} /> Community Vibe Check
      </h3>
      
      <div className="grid grid-cols-3 gap-3">
        {/* BUTTON: LEGIT */}
        <button 
          disabled={votingStatus === 'submitting'}
          onClick={() => handleVote('confirmed')}
          className="flex flex-col items-center justify-center gap-2 p-3 rounded-lg border border-white/10 bg-white/5 hover:bg-emerald-500/10 hover:border-emerald-500/50 hover:text-emerald-400 transition-all group"
        >
          <ShieldCheck size={20} className="text-gray-400 group-hover:text-emerald-400 transition-colors" />
          <span className="text-[10px] font-medium text-gray-300">Legit</span>
        </button>

        {/* BUTTON: SUS */}
        <button 
          disabled={votingStatus === 'submitting'}
          onClick={() => handleVote('sus')}
          className="flex flex-col items-center justify-center gap-2 p-3 rounded-lg border border-white/10 bg-white/5 hover:bg-orange-500/10 hover:border-orange-500/50 hover:text-orange-400 transition-all group"
        >
          <AlertTriangle size={20} className="text-gray-400 group-hover:text-orange-400 transition-colors" />
          <span className="text-[10px] font-medium text-gray-300">Sus</span>
        </button>

        {/* BUTTON: SCAM */}
        <button 
          disabled={votingStatus === 'submitting'}
          onClick={() => handleVote('scam')}
          className="flex flex-col items-center justify-center gap-2 p-3 rounded-lg border border-white/10 bg-white/5 hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-400 transition-all group"
        >
          {votingStatus === 'submitting' ? (
             <Loader2 size={20} className="animate-spin text-gray-400" />
          ) : (
             <Siren size={20} className="text-gray-400 group-hover:text-red-400 transition-colors" />
          )}
          <span className="text-[10px] font-medium text-gray-300">Scam</span>
        </button>
      </div>
    </div>
  );
}
