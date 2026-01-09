import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Copy, Check, X, RefreshCw, Twitter, Linkedin, Instagram, AlertTriangle } from 'lucide-react';

interface HypeManProps {
  property: any;
  onClose: () => void;
}

export default function HypeManModal({ property, onClose }: HypeManProps) {
  const [step, setStep] = useState<'analyzing' | 'generating' | 'done' | 'error'>('analyzing');
  const [copyIndex, setCopyIndex] = useState<number | null>(null);
  const [variations, setVariations] = useState<any[]>([]);

  // --- 🧠 N8N INTEGRATION WITH TRAFFIC DRIVER ---
  const generateStrategies = async () => {
    try {
      // 1. Generate the Traffic Link
      // Automatically detects if you are on localhost or production
      const baseUrl = window.location.origin;
      // Falls back to '0' if ID is missing to prevent broken links
      const safeId = property.id || '0'; 
      const listingUrl = `${baseUrl}/listing/${safeId}`;

      // 2. Construct the Prompt Context
      const price = property.currency === 'USD' 
        ? `$${(property.price || 0).toLocaleString()}` 
        : `₵${(property.price || 0).toLocaleString()}`;
        
      const details = `
        Listing Title: ${property.title || 'Exclusive Listing'}
        Location: ${property.location_name || 'Accra, Ghana'}
        Price: ${price}
        Key Features: ${property.details?.bedrooms || 'N/A'} Beds, ${JSON.stringify(property.features || [])}
        
        IMPORTANT TRAFFIC DRIVER:
        The URL for this listing is: ${listingUrl}
        Please ensure the social posts encourage clicking this link to view full details.
      `.trim();

      // 3. Hit the N8N Production Webhook
      const response = await fetch('https://asta-hypeman-n8n-138443159777.us-central1.run.app/webhook/hypeman', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ property_details: details })
      });

      const data = await response.json();

      // 4. Sanitize & Parse AI Response
      // Strips markdown code blocks if the AI adds them
      let rawText = data.caption || "{}";
      const cleanJson = rawText.replace(/```json/g, '').replace(/```/g, '').trim();
      const aiContent = JSON.parse(cleanJson);

      return [
        {
          platform: 'twitter',
          icon: Twitter,
          label: 'The "FOMO" Tweet',
          text: aiContent.option_1 || "Error generating content."
        },
        {
          platform: 'instagram',
          icon: Instagram,
          label: 'The "Aesthetic" Caption',
          text: aiContent.option_2 || "Error generating content."
        },
        {
          platform: 'linkedin',
          icon: Linkedin,
          label: 'The "Investor" Pitch',
          text: aiContent.option_3 || "Error generating content."
        }
      ];

    } catch (error) {
      console.error("Hypeman Brain Freeze:", error);
      setStep('error');
      return [];
    }
  };

  // --- LIFECYCLE MANAGEMENT ---
  useEffect(() => {
    let isMounted = true;

    const runSequence = async () => {
      setStep('analyzing');
      // Artificial delay for UX pacing (The "Magic" feeling)
      await new Promise(r => setTimeout(r, 1500));
      if (!isMounted) return;
      
      setStep('generating');
      const strategies = await generateStrategies();
      
      if (isMounted && strategies.length > 0) {
        setVariations(strategies);
        setStep('done');
      } else if (isMounted) {
        setStep('error');
      }
    };

    runSequence();
    return () => { isMounted = false; };
  }, []); 

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopyIndex(index);
    setTimeout(() => setCopyIndex(null), 2000);
  };

  const handleRegenerate = async () => {
    setStep('analyzing');
    setTimeout(async () => {
      setStep('generating');
      const strategies = await generateStrategies();
      if (strategies.length > 0) {
        setVariations(strategies);
        setStep('done');
      } else {
        setStep('error');
      }
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg bg-[#0A0A0A] border border-white/10 rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]"
      >
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center border border-purple-500/20">
              <Sparkles size={20} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-white font-bold text-lg tracking-tight">HypeMan AI</h3>
              <p className="text-purple-400 text-xs font-mono uppercase tracking-wider">Marketing Generator</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 relative min-h-[300px]">
          <AnimatePresence mode="wait">
            {step === 'analyzing' && (
              <motion.div 
                key="analyzing"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center text-center p-6"
              >
                <RefreshCw size={40} className="text-purple-500 animate-spin mb-4" />
                <h4 className="text-white font-bold mb-2">Analyzing Asset Data...</h4>
                <p className="text-gray-500 text-xs font-mono">
                  Scanning features: {property.title || "Unknown"}<br/>
                  Location data: {property.location_name || "Unknown"}<br/>
                  Price point: {property.price || "On Request"}
                </p>
              </motion.div>
            )}

            {step === 'generating' && (
              <motion.div 
                key="generating"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center text-center p-6"
              >
                <Sparkles size={40} className="text-white animate-pulse mb-4" />
                <h4 className="text-white font-bold mb-2">Synthesizing Campaigns...</h4>
                <p className="text-gray-500 text-xs font-mono">
                  Drafting viral hooks...<br/>
                  Optimizing hashtags...<br/>
                  Calibrating tone...
                </p>
              </motion.div>
            )}

            {step === 'error' && (
              <motion.div 
                key="error"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="absolute inset-0 flex flex-col items-center justify-center text-center p-6"
              >
                <AlertTriangle size={40} className="text-red-500 mb-4" />
                <h4 className="text-white font-bold mb-2">Connection Interrupted</h4>
                <p className="text-gray-500 text-xs font-mono mb-4">
                  The AI Strategist could not report in.<br/>
                  Check your connection and try again.
                </p>
                <button 
                  onClick={handleRegenerate}
                  className="px-4 py-2 bg-white text-black text-xs font-bold rounded hover:bg-gray-200"
                >
                  Retry Connection
                </button>
              </motion.div>
            )}

            {step === 'done' && (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {variations.map((v, i) => (
                  <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4 hover:border-purple-500/30 transition-colors group">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        <v.icon size={16} className="text-gray-400" />
                        <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">{v.label}</span>
                      </div>
                      <button 
                        onClick={() => handleCopy(v.text, i)}
                        className="text-gray-500 hover:text-white transition-colors"
                        title="Copy to clipboard"
                      >
                        {copyIndex === i ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
                      </button>
                    </div>
                    <div className="bg-black/50 rounded-lg p-3 border border-white/5">
                      <p className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed select-text">
                        {v.text}
                      </p>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {step === 'done' && (
          <div className="p-4 border-t border-white/5 bg-black/40">
            <button 
              onClick={handleRegenerate}
              className="w-full py-3 bg-white hover:bg-gray-200 text-black font-bold rounded-lg flex items-center justify-center gap-2 text-xs uppercase tracking-widest transition-colors"
            >
              <RefreshCw size={14} /> Regenerate Concepts
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
