import React, { useEffect, useState, useRef } from 'react';
import { supabase } from '../../lib/supabase';
import { 
  BarChart3, 
  TrendingUp, 
  Wallet, 
  MousePointer2, 
  Download, 
  Building2, 
  PieChart, 
  ArrowRight, 
  Map, 
  Zap, 
  Activity,
  HelpCircle,
  Send,
  Bot,
  User,
  Loader2
} from 'lucide-react';

export default function ReportsCenter() {
  const [activeTab, setActiveTab] = useState<'partners' | 'market'>('market');
  const [loading, setLoading] = useState(true);
  
  // --- STATE FOR METRICS ---
  const [metrics, setMetrics] = useState({ totalValue: 0, potentialComm: 0, totalLeads: 0, topPartner: { name: '-', count: 0 } });
  const [partnerStats, setPartnerStats] = useState<any[]>([]);
  const [marketStats, setMarketStats] = useState<any[]>([]);
  const [selectedPartnerReport, setSelectedPartnerReport] = useState<string>('all');

  // --- ORACLE CHAT STATE ---
  const [chatHistory, setChatHistory] = useState<{role: 'user' | 'ai', text: string}[]>([
    { role: 'ai', text: "I am the Asta Market Oracle. I have analyzed the live data supply & demand curves. Ask me where to invest next." }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isOracleThinking, setIsOracleThinking] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { runAnalysis(); }, []);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatHistory]);

  async function runAnalysis() {
    setLoading(true);
    // Fetch Data
    const { data: properties } = await supabase.from('properties').select('id, price, currency, status, partner_id, location_name');
    const { data: leads } = await supabase.from('leads').select('id, property_id');
    const { data: partners } = await supabase.from('partners').select('*');

    if (!properties || !leads || !partners) return;

    // A. Platform Metrics
    let totalVal = 0; let totalComm = 0;
    properties.forEach(p => {
      if (p.status === 'active') {
        const price = p.currency === 'USD' ? p.price : p.price / 15; 
        totalVal += price;
        const partner = partners.find(pt => pt.id === p.partner_id);
        totalComm += (price * ((partner?.commission_rate || 5) / 100));
      }
    });

    // B. Partner Leaderboard
    const pStats = partners.map(partner => {
      const partnerProps = properties.filter(p => p.partner_id === partner.id);
      const propIds = partnerProps.map(p => p.id);
      const partnerLeads = leads.filter(l => propIds.includes(l.property_id)).length;
      const partnerValue = partnerProps.reduce((sum, p) => sum + (p.price || 0), 0);
      return {
        id: partner.id, name: partner.name, listingCount: partnerProps.length,
        leadCount: partnerLeads, totalValue: partnerValue,
        activeCount: partnerProps.filter(p => p.status === 'active').length
      };
    }).sort((a, b) => b.leadCount - a.leadCount);

    // C. Market Oracle Data
    const locationMap: Record<string, any> = {};
    properties.forEach(p => {
      const loc = p.location_name || 'Unknown';
      if (!locationMap[loc]) locationMap[loc] = { name: loc, supply: 0, demand: 0, avgPrice: 0, priceSum: 0, count: 0 };
      locationMap[loc].supply++;
      locationMap[loc].priceSum += p.price;
      locationMap[loc].count++;
      locationMap[loc].demand += leads.filter(l => l.property_id === p.id).length;
    });

    const mStats = Object.values(locationMap).map((loc: any) => ({
      name: loc.name,
      supply: loc.supply,
      demand: loc.demand,
      avgPrice: loc.count > 0 ? loc.priceSum / loc.count : 0,
      heatScore: loc.supply > 0 ? (loc.demand / loc.supply).toFixed(1) : "0.0"
    })).sort((a: any, b: any) => b.demand - a.demand).slice(0, 10);

    setMetrics({ totalValue: totalVal, potentialComm: totalComm, totalLeads: leads.length, topPartner: { name: pStats[0]?.name || '-', count: pStats[0]?.leadCount || 0 } });
    setPartnerStats(pStats);
    setMarketStats(mStats);
    setLoading(false);
  }

  const handleAskOracle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userQ = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', text: userQ }]);
    setIsOracleThinking(true);

    try {
      const { data, error } = await supabase.functions.invoke('ask-oracle', {
        body: { query: userQ, context: marketStats }
      });

      if (error) throw error;
      setChatHistory(prev => [...prev, { role: 'ai', text: data.answer }]);
    } catch (err) {
      console.error(err);
      setChatHistory(prev => [...prev, { role: 'ai', text: "⚠️ Connection error. Ensure 'ask-oracle' function is deployed." }]);
    } finally {
      setIsOracleThinking(false);
    }
  };

  const reportView = selectedPartnerReport === 'all' ? partnerStats : partnerStats.filter(p => p.id.toString() === selectedPartnerReport);

  return (
    <div className="space-y-8">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
            <BarChart3 size={24} className="text-emerald-500" />
            Intelligence Center
          </h2>
          <p className="text-gray-500 text-xs font-mono">Data Aggregation & Strategic Analysis</p>
        </div>
        <div className="flex space-x-2 bg-white/5 p-1 rounded-lg">
          <button onClick={() => setActiveTab('market')} className={`px-4 py-2 rounded-md text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2 ${activeTab === 'market' ? 'bg-emerald-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}>
            <Activity size={14} /> Market Oracle
          </button>
          <button onClick={() => setActiveTab('partners')} className={`px-4 py-2 rounded-md text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2 ${activeTab === 'partners' ? 'bg-purple-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}>
            <Building2 size={14} /> Partner ROI
          </button>
        </div>
      </div>

      {/* === TAB 1: MARKET ORACLE === */}
      {activeTab === 'market' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2">
          
          {/* CHAT INTERFACE */}
          <div className="lg:col-span-1 bg-[#111] border border-white/10 rounded-xl flex flex-col h-[600px] overflow-hidden shadow-2xl relative">
            <div className="p-4 border-b border-white/10 bg-emerald-900/10 flex items-center gap-2">
              <Zap size={16} className="text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Ask The Oracle</h3>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'ai' ? 'bg-emerald-600' : 'bg-gray-700'}`}>
                    {msg.role === 'ai' ? <Bot size={16} className="text-white"/> : <User size={16} className="text-white"/>}
                  </div>
                  <div className={`p-3 rounded-xl text-xs leading-relaxed max-w-[85%] ${
                    msg.role === 'ai' ? 'bg-white/10 text-gray-200' : 'bg-emerald-600 text-white'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isOracleThinking && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
                    <Loader2 size={16} className="animate-spin text-white" />
                  </div>
                  <div className="p-3 bg-white/10 rounded-xl text-xs text-gray-400 italic">
                    Analyzing market signals...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <form onSubmit={handleAskOracle} className="p-3 border-t border-white/10 bg-black/20">
              <div className="relative">
                <input 
                  className="w-full bg-[#09090b] border border-white/10 rounded-lg py-3 pl-4 pr-10 text-xs text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  placeholder="Ask about yields, demand gaps, or trends..."
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  disabled={isOracleThinking}
                />
                <button 
                  type="submit"
                  disabled={isOracleThinking}
                  className="absolute right-2 top-2 p-1 text-emerald-500 hover:text-emerald-400 disabled:opacity-50 transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>
            </form>
          </div>

          {/* DATA TABLE */}
          {/* Removed overflow-hidden from outer card to allow tooltips to spill out */}
          <div className="lg:col-span-2 bg-[#111] border border-white/10 rounded-xl shadow-2xl h-[600px] flex flex-col">
            <div className="p-6 border-b border-white/10 flex justify-between items-center shrink-0">
              <div>
                <h3 className="text-lg font-bold text-white">Zone Performance Index</h3>
                <p className="text-xs text-gray-500 mt-1">Real-time Supply vs. Demand analysis</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] text-gray-500 uppercase font-bold">Data Points</p>
                <p className="text-emerald-400 font-mono text-lg font-bold">{metrics.totalLeads + partnerStats.reduce((acc, curr) => acc + curr.listingCount, 0)}</p>
              </div>
            </div>
            
            <div className="overflow-auto flex-1">
              <table className="w-full text-left">
                <thead className="bg-black/40 text-[10px] uppercase text-gray-500 font-bold tracking-widest border-b border-white/5 sticky top-0 backdrop-blur-md z-10">
                  <tr>
                    <th className="p-5">Location Zone</th>
                    <th className="p-5">Supply (Assets)</th>
                    <th className="p-5">Demand (Leads)</th>
                    <th className="p-5">Avg. Valuation</th>
                    <th className="p-5 text-right flex justify-end items-center gap-2 relative group">
                      Heat Score
                      <HelpCircle size={12} className="text-gray-500 cursor-help" />
                      {/* Fixed Tooltip: Z-50, wider width, positioned carefully */}
                      <div className="absolute top-full right-0 mt-2 w-max max-w-[200px] px-3 py-2 bg-gray-800 border border-white/10 text-[9px] text-white rounded shadow-xl text-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 font-normal normal-case">
                        Calculated as Demand (Leads) ÷ Supply (Assets). High score = Opportunity.
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-sm">
                  {loading ? (
                    <tr><td colSpan={5} className="p-8 text-center text-gray-500">Processing...</td></tr>
                  ) : marketStats.map((loc, i) => (
                    <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="p-5 font-bold text-white flex items-center gap-2">
                        <Map size={14} className="text-gray-600 group-hover:text-emerald-500 transition-colors" />
                        {loc.name}
                      </td>
                      <td className="p-5 text-gray-400">{loc.supply} Listings</td>
                      <td className="p-5">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500" style={{ width: `${Math.min(100, loc.demand * 5)}%` }} />
                          </div>
                          <span className="text-xs font-bold text-blue-400">{loc.demand}</span>
                        </div>
                      </td>
                      <td className="p-5 font-mono text-xs text-gray-300">{loc.avgPrice.toLocaleString()}</td>
                      <td className="p-5 text-right">
                        <span className={`px-2 py-1 rounded text-[10px] font-bold border ${
                          parseFloat(loc.heatScore) > 2.0 ? 'bg-red-500/10 text-red-400 border-red-500/20' 
                          : parseFloat(loc.heatScore) > 1.0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-white/5 text-gray-500 border-white/10'
                        }`}>
                          {loc.heatScore}x Saturation
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* === TAB 2: PARTNER REPORTS === */}
      {activeTab === 'partners' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
          {/* KPI GRID - Added hover:z-50 to parent cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[#111] p-5 rounded-xl border border-white/10 relative group hover:z-50 transition-all">
              <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none"><div className="absolute top-0 right-0 p-4 opacity-5"><Wallet size={64} /></div></div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-gray-500 text-[10px] uppercase font-bold tracking-wider">Assets Under Management</p>
                  <div className="group/tooltip relative"><HelpCircle size={10} className="text-gray-600 cursor-help" /><div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] px-3 py-2 bg-gray-800 border border-white/10 text-[9px] text-white rounded text-center opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">Total value of active inventory</div></div>
                </div>
                <h3 className="text-2xl font-bold text-white">${(metrics.totalValue / 1000000).toFixed(1)}M</h3>
              </div>
            </div>
            <div className="bg-[#111] p-5 rounded-xl border border-white/10 relative group hover:z-50 transition-all">
              <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none"><div className="absolute top-0 right-0 p-4 opacity-5"><PieChart size={64} /></div></div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-gray-500 text-[10px] uppercase font-bold tracking-wider">Projected Commission</p>
                  <div className="group/tooltip relative"><HelpCircle size={10} className="text-gray-600 cursor-help" /><div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] px-3 py-2 bg-gray-800 border border-white/10 text-[9px] text-white rounded text-center opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">Potential revenue based on partner rates</div></div>
                </div>
                <h3 className="text-2xl font-bold text-white text-purple-400">${metrics.potentialComm.toLocaleString()}</h3>
              </div>
            </div>
            <div className="bg-[#111] p-5 rounded-xl border border-white/10 relative group">
              <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none"><div className="absolute top-0 right-0 p-4 opacity-5"><MousePointer2 size={64} /></div></div>
              <div className="relative z-10">
                <p className="text-gray-500 text-[10px] uppercase font-bold tracking-wider">Total Lead Volume</p>
                <h3 className="text-2xl font-bold text-white text-blue-400">{metrics.totalLeads}</h3>
              </div>
            </div>
            <div className="bg-[#111] p-5 rounded-xl border border-white/10 relative group">
              <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none"><div className="absolute top-0 right-0 p-4 opacity-5"><Building2 size={64} /></div></div>
              <div className="relative z-10">
                <p className="text-gray-500 text-[10px] uppercase font-bold tracking-wider">Top Performing Partner</p>
                <h3 className="text-xl font-bold text-white truncate">{metrics.topPartner.name}</h3>
              </div>
            </div>
          </div>

          {/* PARTNER TABLE - Removed overflow-hidden */}
          <div className="bg-[#111] border border-white/10 rounded-xl shadow-2xl">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/[0.02]">
              <div><h3 className="text-lg font-bold text-white">Partner Performance Ledger</h3><p className="text-xs text-gray-500 mt-1">Exportable ROI reports</p></div>
              <div className="flex gap-2">
                <select className="bg-black text-white text-xs px-3 py-1.5 rounded outline-none border border-white/10 focus:border-purple-500" value={selectedPartnerReport} onChange={(e) => setSelectedPartnerReport(e.target.value)}><option value="all">Global View</option>{partnerStats.map(p => (<option key={p.id} value={p.id}>{p.name}</option>))}</select>
                <button className="bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-2 transition-colors" onClick={() => window.print()}><Download size={12} /> PDF</button>
              </div>
            </div>
            <div className="overflow-x-auto min-h-[300px]">
              <table className="w-full text-left">
                <thead className="bg-black/40 text-[10px] uppercase text-gray-500 font-bold tracking-widest border-b border-white/5">
                  <tr>
                    <th className="p-5">Partner Agency</th><th className="p-5">Inventory Depth</th><th className="p-5">Portfolio Value</th><th className="p-5">Leads Generated</th>
                    <th className="p-5 text-right flex justify-end items-center gap-2 relative group">Lead Efficiency<div className="group relative"><HelpCircle size={12} className="text-gray-500 cursor-help" /><div className="absolute top-full right-0 mt-2 w-max max-w-[200px] px-3 py-2 bg-gray-800 border border-white/10 text-[9px] text-white rounded text-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 font-normal normal-case shadow-xl">Avg. leads per listing</div></div></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-sm">
                  {reportView.map((p, i) => (
                    <tr key={p.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="p-5"><div className="flex items-center gap-3"><div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs bg-white/10 text-gray-400`}>{i+1}</div><span className="font-bold text-white">{p.name}</span></div></td>
                      <td className="p-5"><div className="flex flex-col"><span className="text-white font-mono">{p.listingCount} Listings</span><span className="text-[10px] text-gray-500">{p.activeCount} Active</span></div></td>
                      <td className="p-5 font-mono text-gray-400">{p.totalValue.toLocaleString()}</td>
                      <td className="p-5"><div className="flex items-center gap-2"><span className="text-purple-400 font-bold text-lg">{p.leadCount}</span><span className="text-[10px] text-purple-500/50 uppercase">Clicks</span></div></td>
                      <td className="p-5 text-right"><span className="px-2 py-1 rounded text-[10px] font-bold border bg-white/5 text-gray-500 border-white/10">{p.listingCount > 0 ? (p.leadCount / p.listingCount).toFixed(1) : 0} Ratio</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
