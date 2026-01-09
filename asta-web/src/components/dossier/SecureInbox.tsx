import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import { 
  Shield, AlertTriangle, Clock, Search, ChevronRight, FileText, Lock, Trash2, Archive, ExternalLink, Loader2 
} from 'lucide-react';
import type { IntelMessage } from '../../hooks/useHunterIntel';

interface SecureInboxProps {
  messages: IntelMessage[];
  loading: boolean;
  onRead: (id: string) => void;
  onViewAsset?: (id: string) => void; 
}

export default function SecureInbox({ messages, loading, onRead, onViewAsset }: SecureInboxProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState(''); 
  const [_, setSearchParams] = useSearchParams(); // Hook for URL updates

  const selectedMessage = messages.find(m => m.id === selectedId);

  const filteredMessages = messages.filter(msg => {
    const term = searchTerm.toLowerCase();
    return (
      msg.subject.toLowerCase().includes(term) ||
      msg.sender.toLowerCase().includes(term) ||
      msg.body.toLowerCase().includes(term)
    );
  });

  const handleSelect = (id: string) => {
    setSelectedId(id);
    onRead(id);
  };

  const handleOpenAsset = (propertyId: string) => {
    if (onViewAsset) {
      onViewAsset(propertyId);
    } else {
      // FIX: Use setSearchParams to switch views WITHOUT reloading the page.
      // We set 'listing_id' which the main map listens for.
      // We do NOT include 'mode=dossier', effectively closing the UCC.
      setSearchParams({ listing_id: propertyId });
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'alert': return <AlertTriangle size={14} className="text-amber-500" />;
      case 'intel': return <FileText size={14} className="text-blue-500" />;
      default: return <Shield size={14} className="text-emerald-500" />;
    }
  };

  if (loading) {
     return (
        <div className="flex h-full items-center justify-center text-emerald-500 flex-col gap-4">
           <Loader2 className="animate-spin w-8 h-8" />
           <p className="text-xs font-mono uppercase animate-pulse">Decrypting Network Traffic...</p>
        </div>
     );
  }

  return (
    <div className="flex h-full bg-black/20 text-white font-sans overflow-hidden">
      
      {/* --- LEFT PANE: LIST --- */}
      <div className={`${selectedId ? 'hidden md:flex' : 'flex'} w-full md:w-2/5 flex-col border-r border-white/10`}>
        
        {/* Search Header */}
        <div className="p-3 border-b border-white/10 bg-white/5">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={12} />
            <input 
              type="text" 
              placeholder="Search logs..." 
              value={searchTerm} 
              onChange={(e) => setSearchTerm(e.target.value)} 
              className="w-full bg-black/50 border border-white/10 rounded-md py-1.5 pl-8 pr-3 text-xs text-gray-300 focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {filteredMessages.length > 0 ? (
            filteredMessages.map((msg) => (
              <div 
                key={msg.id}
                onClick={() => handleSelect(msg.id)}
                className={`p-4 border-b border-white/5 cursor-pointer hover:bg-white/5 transition-colors group relative ${
                  selectedId === msg.id ? 'bg-white/10' : ''
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-2 ${msg.status === 'unread' ? 'text-emerald-400' : 'text-gray-500'}`}>
                    {getIcon(msg.type)} {msg.sender}
                  </span>
                  <span className="text-[9px] text-gray-600 font-mono">{msg.timestamp}</span>
                </div>
                <h4 className={`text-xs font-medium mb-1 truncate ${msg.status === 'unread' ? 'text-white' : 'text-gray-400'}`}>
                  {msg.subject}
                </h4>
                <p className="text-[10px] text-gray-500 line-clamp-2 leading-relaxed">
                  {msg.preview}
                </p>
                
                {selectedId === msg.id && (
                  <motion.div layoutId="activeLine" className="absolute left-0 top-0 bottom-0 w-0.5 bg-emerald-500" />
                )}
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-gray-500 text-xs font-mono">
               No matching records found.
            </div>
          )}
        </div>
      </div>

      {/* --- RIGHT PANE: READER --- */}
      <div className={`${!selectedId ? 'hidden md:flex' : 'flex'} flex-1 flex-col bg-black/40 relative`}>
        {selectedMessage ? (
          <>
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex justify-between items-start bg-white/5">
              <div>
                <button 
                  onClick={() => setSelectedId(null)} 
                  className="md:hidden mb-4 text-gray-500 hover:text-white flex items-center gap-1 text-xs"
                >
                  <ChevronRight className="rotate-180" size={12} /> Back
                </button>
                <h2 className="text-lg font-bold text-white mb-2">{selectedMessage.subject}</h2>
                <div className="flex items-center gap-3 text-xs text-gray-400 font-mono">
                  <span className="flex items-center gap-1 text-emerald-500">
                    {getIcon(selectedMessage.type)} {selectedMessage.sender}
                  </span>
                  <span>|</span>
                  <span className="uppercase text-[9px] border border-gray-700 px-1.5 rounded">{selectedMessage.priority} Priority</span>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="flex-1 p-8 overflow-y-auto">
              <div className="max-w-2xl text-sm leading-7 text-gray-300 font-mono whitespace-pre-line">
                {selectedMessage.body}
              </div>

              {/* Action Button: View Property */}
              {selectedMessage.property_id && (
                 <div className="mt-8">
                    <button 
                       onClick={() => handleOpenAsset(selectedMessage.property_id!)}
                       className="bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 border border-blue-500/50 px-4 py-2 rounded flex items-center gap-2 text-xs font-bold uppercase tracking-wider transition-all"
                    >
                       <ExternalLink size={14} /> Open Asset Dossier
                    </button>
                 </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-white/10 bg-black flex justify-between items-center px-4">
              <span className="text-[9px] text-emerald-900 uppercase font-bold flex items-center gap-2">
                <Lock size={8} /> End-to-End Encrypted
              </span>
              <span className="text-[9px] text-gray-700 font-mono">
                ID: {selectedMessage.id}
              </span>
            </div>
          </>
        ) : (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center text-gray-600">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
               <Shield size={24} className="opacity-20" />
            </div>
            <p className="text-xs font-mono uppercase tracking-widest">Secure Link Established</p>
            <p className="text-[10px] mt-2">Select a transmission to decrypt</p>
          </div>
        )}
      </div>

    </div>
  );
}
