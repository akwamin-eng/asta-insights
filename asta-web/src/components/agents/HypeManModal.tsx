import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Copy,
  Check,
  X,
  RefreshCw,
  Twitter,
  Linkedin,
  Instagram,
  BrainCircuit,
  Bot
} from "lucide-react";
import { GoogleGenerativeAI } from "@google/generative-ai";

interface HypeManProps {
  property: any;
  onClose: () => void;
}

// 🟢 SECURITY FIX: No hardcoded fallback. 
// If VITE_GOOGLE_API_KEY is missing in .env, this is empty.
const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY || "";

export default function HypeManModal({ property, onClose }: HypeManProps) {
  const [step, setStep] = useState<"analyzing" | "generating" | "done">("analyzing");
  const [copyIndex, setCopyIndex] = useState<number | null>(null);
  const [variations, setVariations] = useState<any[]>([]);
  const [isSimulation, setIsSimulation] = useState(false);

  // --- 🧬 SIMULATION DATA (Safe Fallback) ---
  const generateMockStrategies = () => {
    return [
      {
        platform: "twitter",
        icon: Twitter,
        label: 'The "FOMO" Tweet',
        text: `🚨 JUST LISTED: ${property.title} in ${property.location_name}! \n\n💎 ${property.currency} ${property.price.toLocaleString()} \n👀 Views are insane. This won't last 48hrs. \n\nDM me or check the link below 👇 #RealEstate #Ghana #${property.location_name.replace(/\s/g, '')}`
      },
      {
        platform: "instagram",
        icon: Instagram,
        label: 'The "Aesthetic" Caption',
        text: `POV: You wake up here. 🌅✨\n\n📍 ${property.location_name}\n💰 ${property.currency} ${property.price.toLocaleString()}\n\nIs this the dream or what? Tag the person you'd move in with. 👇\n\n#DreamHome #GhanaLuxury #RealEstate`
      },
      {
        platform: "linkedin",
        icon: Linkedin,
        label: 'The "Investor" Pitch',
        text: `Exciting investment opportunity in the heart of ${property.location_name}.\n\nProperty: ${property.title}\nAsk: ${property.currency} ${property.price.toLocaleString()}\n\nWith current market trends in Accra, this asset is positioned for significant capital appreciation. Contact for the dossier.`
      }
    ];
  };

  // --- 🧠 AI GENERATION LOGIC ---
  const generateStrategies = async () => {
    // 🟢 SECURITY CHECK: If no key, throw immediately to trigger simulation
    if (!API_KEY) throw new Error("Missing API Key");

    const genAI = new GoogleGenerativeAI(API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const baseUrl = window.location.origin;
    const safeId = property.id || "0";
    const listingUrl = `${baseUrl}/listing/${safeId}`;
    const price = property.currency === "USD" ? `$${(property.price || 0).toLocaleString()}` : `₵${(property.price || 0).toLocaleString()}`;

    const prompt = `
      Act as a viral Real Estate Marketer. Write 3 distinct social media posts.
      DETAILS: Title: ${property.title}, Location: ${property.location_name}, Price: ${price}, Link: ${listingUrl}
      RETURN STRICT JSON: { "option_1": "Twitter post", "option_2": "Instagram post", "option_3": "LinkedIn post" }
    `;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    const cleanJson = text.replace(/```json/g, "").replace(/```/g, "").trim();
    const aiContent = JSON.parse(cleanJson);

    return [
      { platform: "twitter", icon: Twitter, label: 'The "FOMO" Tweet', text: aiContent.option_1 },
      { platform: "instagram", icon: Instagram, label: 'The "Aesthetic" Caption', text: aiContent.option_2 },
      { platform: "linkedin", icon: Linkedin, label: 'The "Investor" Pitch', text: aiContent.option_3 },
    ];
  };

  // --- LIFECYCLE ---
  useEffect(() => {
    let isMounted = true;
    const runSequence = async () => {
      setStep("analyzing");
      await new Promise((r) => setTimeout(r, 1500));
      
      if (!isMounted) return;
      setStep("generating");

      try {
        const strategies = await generateStrategies();
        if (isMounted) {
          setVariations(strategies);
          setIsSimulation(false);
          setStep("done");
        }
      } catch (err) {
        console.warn("Hypeman: Switching to Offline Mode (No API Key or Error).");
        if (isMounted) {
          setVariations(generateMockStrategies());
          setIsSimulation(true);
          setStep("done");
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

  return (
    <div className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg bg-[#0A0A0A] border border-white/10 rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center border border-purple-500/20"><Sparkles size={20} className="text-purple-400" /></div>
            <div><h3 className="text-white font-bold text-lg tracking-tight">HypeMan AI</h3><p className="text-purple-400 text-xs font-mono uppercase tracking-wider">Marketing Generator</p></div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors"><X size={20} /></button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 relative min-h-[300px]">
          <AnimatePresence mode="wait">
            {step === "analyzing" && (
              <motion.div key="analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
                <div className="relative"><div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full animate-pulse" /><BrainCircuit size={48} className="text-purple-500 relative z-10 animate-pulse" /></div>
                <h4 className="text-white font-bold mt-6 mb-2">Analyzing Asset Vibe...</h4><p className="text-gray-500 text-xs font-mono">Connecting to Neural Net...</p>
              </motion.div>
            )}

            {step === "generating" && (
              <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
                <Sparkles size={48} className="text-white animate-spin-slow mb-4" /><h4 className="text-white font-bold mb-2">Drafting Viral Hooks...</h4>
              </motion.div>
            )}

            {step === "done" && (
              <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4 w-full">
                {isSimulation && (
                  <div className="bg-yellow-500/10 border border-yellow-500/20 p-3 rounded-lg text-center mb-2 flex items-center justify-center gap-2">
                    <Bot size={14} className="text-yellow-400" />
                    <p className="text-[10px] text-yellow-400 font-bold uppercase tracking-wider">Offline Mode Active</p>
                  </div>
                )}
                {variations.map((v, i) => (
                  <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} className="bg-white/5 border border-white/10 rounded-xl p-4 hover:border-purple-500/30 transition-all group hover:bg-white/[0.07]">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded-lg bg-black/40 ${v.platform === 'twitter' ? 'text-blue-400' : v.platform === 'instagram' ? 'text-pink-400' : 'text-blue-600'}`}><v.icon size={16} /></div>
                        <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">{v.label}</span>
                      </div>
                      <button onClick={() => handleCopy(v.text, i)} className="p-2 rounded-lg hover:bg-white/10 text-gray-500 hover:text-white transition-colors" title="Copy">{copyIndex === i ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}</button>
                    </div>
                    <div className="bg-black/40 rounded-lg p-3 border border-white/5 group-hover:border-white/10 transition-colors"><p className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed selection:bg-purple-500/30">{v.text}</p></div>
                  </motion.div>
                ))}
                
                <div className="pt-4 flex justify-center">
                  <button onClick={() => { setStep("analyzing"); setTimeout(() => setStep("done"), 1000); }} className="flex items-center gap-2 text-xs font-bold text-gray-500 hover:text-purple-400 transition-colors uppercase tracking-wider">
                    <RefreshCw size={12} /> Regenerate Ideas
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
