import React, { useState, useEffect, useMemo } from "react";
import {
  X,
  MapPin,
  MessageSquare,
  ShieldCheck,
  ChevronDown,
  ArrowLeft,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Send,
  User,
  Phone,
  Sparkles,
  Loader2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { supabase } from '../lib/supabase';
import AuthOverlay from './AuthOverlay';
import Toast from './ui/Toast';
import FieldReportModal from "./dossier/FieldReportModal";
import HypeManModal from "./agents/HypeManModal";

import IntelligenceCard from "./dossier/modules/IntelligenceCard";
import SaveButton from "./SaveButton";
import TrustScorecard from "./intel/TrustScorecard"; 
import MarketPulse from "./intel/MarketPulse";
import TrueCostCalculator from "./intel/TrueCostCalculator";

import { useLeadRouter } from '../hooks/useLeadRouter';

interface PropertyInspectorProps {
  property: any;
  onClose: () => void;
  onVerify?: () => void;
}

export default function PropertyInspector({
  property,
  onClose,
  onVerify,
}: PropertyInspectorProps) {
  // --- UI STATE ---
  const [currency, setCurrency] = useState<"GHS" | "USD">("GHS");
  const [isImageExpanded, setIsImageExpanded] = useState(false);
  const [photoIndex, setPhotoIndex] = useState(0);

  // --- AUTH & GATEKEEPER STATE ---
  const [user, setUser] = useState<any>(null);
  const [showAuth, setShowAuth] = useState(false);
  
  // --- AGENTS & MODALS STATE ---
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [showHypeMan, setShowHypeMan] = useState(false); 
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // --- CONTACT FORM STATE ---
  const [isContactOpen, setContactOpen] = useState(false);
  const [inquirer, setInquirer] = useState({ name: "", phone: "", message: "" });
  
  // LEAD ROUTER HOOK
  const { createLeadAndRedirect, loading: routingLead } = useLeadRouter();

  const data = property;

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      if (data.user?.user_metadata?.full_name) {
        setInquirer(prev => ({ ...prev, name: data.user.user_metadata.full_name }));
      }
    });
  }, []);

  const handleGatekeptAction = (action: () => void) => {
    if (user) {
      action();
    } else {
      setShowAuth(true);
    }
  };

  // Check if current user owns this asset
  const isOwner = user && data.owner_id === user.id;

  if (!data) return null;

  // --- IMAGE GALLERY LOGIC ---
  const galleryImages = useMemo(() => {
    const images: string[] = [];
    if (data.cover_image_url) images.push(data.cover_image_url);
    const extraImages = data.images || data.property_images;
    if (Array.isArray(extraImages)) {
      extraImages.forEach((img: any) => {
        const url = typeof img === "string" ? img : img.url;
        if (url && url !== data.cover_image_url) images.push(url);
      });
    }
    if (images.length === 0) {
      images.push("https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1600&q=80");
    }
    return images;
  }, [data]);

  const nextPhoto = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setPhotoIndex((prev) => (prev + 1) % galleryImages.length);
  };

  const prevPhoto = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setPhotoIndex((prev) => (prev - 1 + galleryImages.length) % galleryImages.length);
  };

  // --- ACTIONS ---
  
  const handleOpenContact = () => {
    setInquirer(prev => ({
      ...prev,
      message: `Hello, I am interested in ${data.title} (${data.location_name}). Is it available for viewing?`
    }));
    setContactOpen(true);
  };

  const handleSendInquiry = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await createLeadAndRedirect(data, inquirer, user);
    if (result.success) {
      setContactOpen(false);
      setToastMessage("Secure Link Established: Redirecting to WhatsApp...");
    } else {
      setToastMessage("Connection Failed. Please try again.");
    }
  };

  const getSafeFeatures = () => {
    try {
      if (!data.vibe_features) return [];
      if (Array.isArray(data.vibe_features)) return data.vibe_features;
      return JSON.parse(data.vibe_features) || [];
    } catch (e) {
      return [];
    }
  };

  const exchangeRate = 15.5;
  const displayPrice =
    currency === "GHS"
      ? `₵${data.price?.toLocaleString()}`
      : `$${(data.price / exchangeRate).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
      
  const numericPrice = currency === "GHS" ? data.price : (data.price / exchangeRate);

  const widgetHoverEffect = "transition-transform duration-300 hover:scale-[1.02] hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)]";

  // MOBILE vs DESKTOP ANIMATION VARIANTS
  const inspectorVariants = {
    hidden: { 
      y: "100%", // Default hidden state for mobile (bottom sheet)
      x: 0,
      opacity: 0 
    },
    visible: { 
      y: 0,
      x: 0,
      opacity: 1 
    },
    desktopHidden: {
      x: "100%", // Hidden state for desktop (side drawer)
      y: 0,
      opacity: 0
    }
  };

  // Simple check for mobile viewport
  const isMobile = window.innerWidth < 768;

  return (
    <>
      <AnimatePresence>{showAuth && <AuthOverlay onClose={() => setShowAuth(false)} />}</AnimatePresence>
      <AnimatePresence>{toastMessage && <Toast message={toastMessage} onClose={() => setToastMessage(null)} type="success" />}</AnimatePresence>
      
      <AnimatePresence>
        {showVerifyModal && (
          <FieldReportModal 
            propertyId={data.id} 
            propertyName={data.title}
            onClose={() => setShowVerifyModal(false)}
            onSuccess={() => setToastMessage("Field Report Transmitted: Reputation Increased")}
          />
        )}
        {showHypeMan && (
          <HypeManModal 
            property={data} 
            onClose={() => setShowHypeMan(false)} 
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isImageExpanded && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[120] bg-black flex items-center justify-center p-0 md:p-4 backdrop-blur-xl"
            onClick={() => setIsImageExpanded(false)}
          >
            <button className="absolute top-6 right-6 text-white bg-black/50 p-3 rounded-full z-50 hover:bg-white hover:text-black transition-colors"><X size={24} /></button>
            {galleryImages.length > 1 && (
              <>
                <button onClick={prevPhoto} className="absolute left-4 top-1/2 -translate-y-1/2 text-white bg-black/50 p-4 rounded-full z-50"><ChevronLeft size={32} /></button>
                <button onClick={nextPhoto} className="absolute right-4 top-1/2 -translate-y-1/2 text-white bg-black/50 p-4 rounded-full z-50"><ChevronRight size={32} /></button>
              </>
            )}
            <img key={photoIndex} src={galleryImages[photoIndex]} className="max-w-full max-h-full md:rounded-lg object-contain pointer-events-none" alt="Gallery" />
            <div className="absolute bottom-0 left-0 w-full p-8 bg-gradient-to-t from-black to-transparent text-center pb-12">
              <p className="text-white text-lg font-bold tracking-tight">{data.title}</p>
              <p className="text-emerald-400 font-mono text-xs mt-1 uppercase tracking-widest">Image {photoIndex + 1} / {galleryImages.length}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        key="property-inspector"
        initial={isMobile ? "hidden" : "desktopHidden"}
        animate="visible"
        exit={isMobile ? "hidden" : "desktopHidden"}
        variants={inspectorVariants}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed inset-0 top-[10vh] md:top-0 md:left-auto md:w-[450px] bg-[#0A0A0A] border-t md:border-t-0 md:border-l border-white/10 shadow-2xl z-[60] flex flex-col rounded-t-2xl md:rounded-none"
      >
        {/* Mobile Drag Handle */}
        <div className="md:hidden w-full flex justify-center pt-3 pb-1 cursor-grab active:cursor-grabbing bg-[#0A0A0A]">
          <div className="w-12 h-1.5 bg-white/20 rounded-full" />
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar pb-32"> 
          
          <div className="relative h-56 md:h-64 bg-gray-900 group cursor-zoom-in" onClick={() => { setPhotoIndex(0); setIsImageExpanded(true); }}>
            <img src={data.cover_image_url || galleryImages[0]} alt={data.title} className="w-full h-full object-cover opacity-90" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] via-transparent to-transparent" />
            
            <div className="absolute top-0 left-0 w-full p-4 flex justify-between items-start z-10">
               <button onClick={(e) => { e.stopPropagation(); onClose(); }} className="bg-black/40 hover:bg-black/80 text-white p-2.5 rounded-full backdrop-blur-md border border-white/10">
                 {/* Mobile gets ChevronDown, Desktop gets ArrowLeft */}
                 {isMobile ? <ChevronDown size={20} /> : <ArrowLeft size={20} />}
               </button>
               
               <div className="flex gap-2">
                 {/* 🟢 GENTLE UPDATE: ONLY SHOW IF OWNER */}
                 {isOwner && (
                   <button 
                     onClick={(e) => { e.stopPropagation(); setShowHypeMan(true); }}
                     className="bg-black/40 hover:bg-purple-500/80 text-white p-2.5 rounded-full backdrop-blur-md border border-white/10 transition-colors"
                     title="Generate Marketing"
                   >
                     <Sparkles size={18} />
                   </button>
                 )}

                 <div className="bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20 text-white text-[10px] font-bold uppercase tracking-wider flex items-center gap-2">
                   <Maximize2 size={12} /> {photoIndex + 1}/{galleryImages.length}
                 </div>
               </div>
            </div>

            <div className="absolute bottom-0 left-0 w-full p-6 pt-12 bg-gradient-to-t from-[#0A0A0A] to-transparent">
              <h2 className="text-2xl md:text-3xl font-bold text-white leading-tight mb-2 tracking-tight">{data.title}</h2>
              <div className="flex items-center text-gray-400 text-sm font-medium">
                <MapPin size={14} className="mr-1 text-emerald-500" />{data.location_name}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-[1fr_auto_auto] gap-3 p-4 border-b border-white/10 bg-[#0A0A0A] sticky top-0 z-20 shadow-lg shadow-black/50">
            <div 
              className="flex flex-col justify-center cursor-pointer active:scale-95 transition-transform" 
              onClick={() => setCurrency((c) => (c === "GHS" ? "USD" : "GHS"))}
            >
              <div className="flex items-center gap-1 text-[10px] text-gray-500 uppercase font-bold tracking-wider">
                Asking Price <ChevronDown size={10} />
              </div>
              <div className="text-xl md:text-2xl font-mono text-emerald-400 font-bold leading-none mt-1">
                {displayPrice}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
               <div onClickCapture={(e) => !user && (e.stopPropagation(), setShowAuth(true))}>
                 <SaveButton propertyId={data.id} className="h-10 w-10 md:w-auto md:px-4" />
               </div>
               
               {onVerify && (
                <button 
                  onClick={() => handleGatekeptAction(() => setShowVerifyModal(true))} 
                  className="w-10 h-10 flex items-center justify-center rounded-lg bg-emerald-900/20 hover:bg-emerald-900/40 border border-emerald-500/30 text-emerald-500 transition-colors"
                >
                  <ShieldCheck size={20} />
                </button>
               )}
            </div>
          </div>

          <div className="p-4 md:p-6 space-y-6 md:space-y-8">
            <AnimatePresence>
              {isContactOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="bg-white/5 border border-emerald-500/30 rounded-xl p-4 md:p-5 space-y-4 relative">
                     <button type="button" onClick={() => setContactOpen(false)} className="absolute top-4 right-4 text-gray-500 hover:text-white bg-white/5 p-1 rounded-full"><X size={14} /></button>
                     <div>
                       <h4 className="text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">Secure Inquiry</h4>
                       <p className="text-gray-500 text-[10px]">Direct encrypted link to agent.</p>
                     </div>
                     <form onSubmit={handleSendInquiry} className="space-y-3">
                        <div className="relative group">
                          <User size={14} className="absolute left-3 top-3 text-gray-500 group-focus-within:text-emerald-500" />
                          <input type="text" required placeholder="Your Name" value={inquirer.name} onChange={(e) => setInquirer({...inquirer, name: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-lg py-2.5 pl-9 pr-3 text-sm text-white focus:border-emerald-500/50 focus:outline-none transition-colors" />
                        </div>
                        <div className="relative group">
                          <Phone size={14} className="absolute left-3 top-3 text-gray-500 group-focus-within:text-emerald-500" />
                          <input type="tel" required placeholder="Phone Number" value={inquirer.phone} onChange={(e) => setInquirer({...inquirer, phone: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-lg py-2.5 pl-9 pr-3 text-sm text-white focus:border-emerald-500/50 focus:outline-none transition-colors" />
                        </div>
                        <textarea required rows={3} value={inquirer.message} onChange={(e) => setInquirer({...inquirer, message: e.target.value})} className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-white focus:border-emerald-500/50 focus:outline-none resize-none" />
                        <button type="submit" disabled={routingLead} className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors uppercase tracking-widest text-xs">
                           {routingLead ? <><Loader2 size={14} className="animate-spin" /> Securing Link...</> : <><Send size={14} /> Send Request</>}
                        </button>
                     </form>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="space-y-4">
                <div>
                  <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">The Brief</h3>
                  <p className="text-gray-300 text-sm leading-relaxed">{data.description_enriched || data.description || "No description provided."}</p>
                </div>
                {data.vibe_features && (
                  <div className="flex flex-wrap gap-2">
                    {getSafeFeatures().map((tag: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[10px] text-gray-400 uppercase tracking-wide">{tag}</span>
                    ))}
                  </div>
                )}
            </div>

            <div className="space-y-4 pt-4 border-t border-white/5">
                <h3 className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-2 flex items-center gap-2"><ShieldCheck size={14} /> Field Intelligence</h3>
                <div className={widgetHoverEffect}><TrustScorecard property={data} owner={data.owner} /></div>
                <div className={widgetHoverEffect}><MarketPulse property={data} /></div>
                <div className={widgetHoverEffect}><TrueCostCalculator price={numericPrice} currency={currency} bedrooms={data.details?.bedrooms || 1} type={data.type} /></div>
            </div>

            <div className="space-y-4 pb-8">
                <IntelligenceCard key={data.id} propertyId={data.id} locationName={data.location_name} />
                <div className="bg-orange-500/5 border border-orange-500/20 rounded-xl p-4 flex gap-3">
                  <AlertTriangle size={16} className="text-orange-500 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-orange-400 text-[10px] font-bold uppercase tracking-wider mb-1">Asta Advisor</h3>
                    <p className="text-xs text-gray-400 leading-relaxed">{data.type === "rent" ? "Standard practice: 1-2 years rent in advance. Demand a contract." : "Critical: Verify Land Title Certificate at Lands Commission before any deposit."}</p>
                  </div>
                </div>
            </div>
          </div>
        </div>

        {!isContactOpen && (
          <div className="absolute bottom-0 left-0 w-full p-4 bg-[#0A0A0A] border-t border-white/10 backdrop-blur-xl pb-8 md:pb-4 z-50">
            <button onClick={handleOpenContact} className="w-full bg-white text-black font-bold py-3.5 rounded-xl hover:bg-emerald-400 flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] active:scale-[0.98]">
              <MessageSquare size={18} className="fill-current" />
              <span className="text-sm uppercase tracking-wider">Contact Agent</span>
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}
