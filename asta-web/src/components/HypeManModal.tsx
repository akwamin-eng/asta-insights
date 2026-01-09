import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Copy, Check, X, RefreshCw, Twitter, Linkedin, Instagram, AlertTriangle } from 'lucide-react';
import { GoogleGenerativeAI } from "@google/generative-ai";

interface HypeManProps {
  property: any;
  onClose: () => void;
}

const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY || "AIzaSyCUQ3Oy0kxzvIT2HaQdSZq3Dst7cf5-ZxQ";
const genAI = new GoogleGenerativeAI(API_KEY);

export default function HypeManModal({ property, onClose }: HypeManProps) {
  const [step, setStep] = useState<'analyzing' | 'generating' | 'done' | 'error'>('analyzing');
  const [copyIndex, setCopyIndex] = useState<number | null>(null);
  const [variations, setVariations] = useState<any[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const generateStrategies = async () => {
    try {
      console.log("🚀 Hypeman: Calling Gemini 2.0 Flash...");
      
      const baseUrl = window.location.origin;
      const safeId = property.id || '0'; 
      const listingUrl = `${baseUrl}/listing/${safeId}`;
      const price = property.currency === 'USD' 
        ? `$${(property.price || 0).toLocaleString()}` 
        : `₵${(property.price || 0).toLocaleString()}`;
        
      const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

      const prompt = `
        Act as a viral Real Estate Marketer. Write 3 distinct social media posts.
        DETAILS: Title: ${property.title}, Location: ${property.location_name}, Price: ${price}.
        LINK: ${listingUrl}
        
        INSTRUCTIONS:
        1. (Twitter): Punchy, FOMO, max 280 chars.
        2. (Instagram): Aesthetic, emoji heavy.
        3. (LinkedIn): Professional, investment focus.

        RETURN STRICT JSON ONLY:
        { "option_1": "...", "option_2": "...", "option_3": "..." }
      `;

      const result = await model.generateContent(prompt);
      const response = await result.response;
      const text = response.text();
      const cleanJson = text.replace(/```json/g, '').replace(/```/g, '').trim();
      const aiContent = JSON.parse(cleanJson);

      return [
        { platform: 'twitter', icon: Twitter, label: 'The "FOMO" Tweet', text: aiContent.option_1 },
        { platform: 'instagram', icon: Instagram, label: 'The "Aesthetic" Caption', text: aiContent.option_2 },
        { platform: 'linkedin', icon: Linkedin, label: 'The "Investor" Pitch', text: aiContent.option_3 }
      ];

    } catch (error: any) {
      console.error("❌ Hypeman Error:", error);
      setErrorMessage(error.message);
      return [];
    }
  };

  useEffect(() => {
    let isMounted = true;
    const runSequence = async () => {
      setStep('analyzing');
      await new Promise(r => setTimeout(r, 1000));
      if (!isMounted) return;
      setStep('generating');
      const strategies = await generateStrategies();
      if (isMounted) {
        if (strategies.length > 0) {
          setVariations(strategies);
          setStep('done');
        } else {
          setStep('error');
        }
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
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg bg-[#0A0A0A] border border-white/10 rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
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
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors"><X size={20} /></button>
        </div>
        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 relative min-h-[300px]">
          <AnimatePresence mode="wait">
            {step === 'analyzing' && (
              <motion.div key="analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
                <RefreshCw size={40} className="text-purple-500 animate-spin mb-4" />
                <h4 className="text-white font-bold mb-2">Analyzing Asset Data...</h4>
                <p className="text-gray-500 text-xs font-mono">Initializing Gemini 2.0 Flash...</p>
              </motion.div>
            )}
            {step === 'generating' && (
              <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
                <Sparkles size={40} className="text-white animate-pulse mb-4" />
                <h4 className="text-white font-bold mb-2">Synthesizing Campaigns...</h4>
              </motion.div>
            )}
            {step === 'error' && (
              <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
                <AlertTriangle size={40} className="text-red-500 mb-4" />
                <h4 className="text-white font-bold mb-2">Hypeman Error</h4>
                <p className="text-xs text-red-300 bg-red-900/20 p-2 rounded border border-red-500/20 mb-4">{errorMessage}</p>
                <button onClick={handleRegenerate} className="px-4 py-2 bg-white text-black text-xs font-bold rounded hover:bg-gray-200">Retry</button>
              </motion.div>
            )}
            {step === 'done' && (
              <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                {variations.map((v, i) => (
                  <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4 hover:border-purple-500/30 transition-colors group">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        <v.icon size={16} className="text-gray-400" />
                        <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">{v.label}</span>
                      </div>
                      <button onClick={() => handleCopy(v.text, i)} className="text-gray-500 hover:text-white transition-colors">
                        {copyIndex === i ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
                      </button>
                    </div>
                    <div className="bg-black/50 rounded-lg p-3 border border-white/5">
                      <p className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed select-text">{v.text}</p>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
