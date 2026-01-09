import React, { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabase';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Edit, 
  Trash2, 
  Eye, 
  Filter, 
  Search, 
  MoreHorizontal,
  ExternalLink,
  MapPin,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Building2 // 👈 New Icon
} from 'lucide-react';
import SubmitIntelModal from '../../components/dossier/SubmitIntelModal'; 

export default function AssetManager() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  
  // Edit State
  const [editingAsset, setEditingAsset] = useState<any>(null);

  useEffect(() => {
    fetchAssets();
  }, []);

  async function fetchAssets() {
    setLoading(true);
    // 🔗 Updated Query: Fetch Partner details alongside Profile details
    const { data, error } = await supabase
      .from('properties')
      .select('*, profiles:owner_id(full_name, email), partners(name, commission_rate)') 
      .order('created_at', { ascending: false });

    if (!error && data) {
      setAssets(data);
    }
    setLoading(false);
  }

  // --- ACTIONS ---

  const handleVerifyToggle = async (id: number, currentStatus: boolean) => {
    setAssets(prev => prev.map(a => a.id === id ? { ...a, verified: !currentStatus } : a));
    
    await supabase
      .from('properties')
      .update({ verified: !currentStatus }) 
      .eq('id', id);
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    setAssets(prev => prev.map(a => a.id === id ? { ...a, status: newStatus } : a));
    await supabase.from('properties').update({ status: newStatus }).eq('id', id);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("CONFIRM DELETION: This action cannot be undone.")) return;
    
    setAssets(prev => prev.filter(a => a.id !== id));
    await supabase.from('properties').delete().eq('id', id);
  };

  // --- FILTERING ---
  const filteredAssets = assets.filter(asset => {
    const matchesSearch = 
      asset.title?.toLowerCase().includes(search.toLowerCase()) ||
      asset.location_name?.toLowerCase().includes(search.toLowerCase()) ||
      asset.profiles?.email?.toLowerCase().includes(search.toLowerCase()) ||
      asset.partners?.name?.toLowerCase().includes(search.toLowerCase()) || // 👈 Search Partner
      asset.details?.external_id?.toLowerCase().includes(search.toLowerCase()); // 👈 Search Ref ID
    
    const matchesFilter = filterStatus === 'all' || asset.status === filterStatus;

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      
      {/* HEADER & CONTROLS */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Asset Governance</h2>
          <p className="text-gray-500 text-xs">Total Database: {assets.length} Records</p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-2.5 text-gray-500 w-4 h-4" />
            <input 
              type="text" 
              placeholder="Search ID, Ref, Partner..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#111] border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-emerald-500/50"
            />
          </div>
          
          <div className="flex bg-[#111] border border-white/10 rounded-lg p-1">
            {['all', 'active', 'draft', 'scam'].map(status => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`px-3 py-1.5 text-[10px] uppercase font-bold rounded transition-all ${
                  filterStatus === status 
                    ? 'bg-white/10 text-white' 
                    : 'text-gray-500 hover:text-gray-300'
                }`}
                title={`Filter view to ${status} listings only`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* THE MASTER TABLE */}
      <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-white/10 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                <th className="p-4 w-12">IMG</th>
                <th className="p-4 w-24">Ref ID</th> {/* 👈 New Column */}
                <th className="p-4">Asset Details</th>
                <th className="p-4">Ownership</th> {/* 👈 Updated Label */}
                <th className="p-4">Status</th>
                <th className="p-4">Price</th>
                <th className="p-4 text-right">Command</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-gray-300">
              {loading ? (
                <tr><td colSpan={7} className="p-8 text-center text-gray-500">Scanning Database...</td></tr>
              ) : filteredAssets.map((asset) => (
                <tr key={asset.id} className="hover:bg-white/[0.02] transition-colors group">
                  
                  {/* IMAGE */}
                  <td className="p-4">
                    <div className="w-10 h-10 bg-white/10 rounded overflow-hidden">
                      {asset.image_urls?.[0] && (
                        <img src={asset.image_urls[0]} alt="" className="w-full h-full object-cover" />
                      )}
                    </div>
                  </td>

                  {/* 🆕 REF ID */}
                  <td className="p-4">
                    {asset.details?.external_id ? (
                      <span className="font-mono text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">
                        {asset.details.external_id}
                      </span>
                    ) : (
                      <span className="text-gray-600 font-mono text-[10px]">-</span>
                    )}
                  </td>

                  {/* DETAILS */}
                  <td className="p-4 max-w-xs">
                    <div className="font-bold text-white truncate" title={asset.title}>{asset.title}</div>
                    <div className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
                      <MapPin size={10} />
                      <span className="truncate">{asset.location_name}</span>
                    </div>
                  </td>

                  {/* 🆕 OWNERSHIP (Partner vs Individual) */}
                  <td className="p-4">
                    {asset.partners ? (
                      <div>
                        <div className="text-xs font-bold text-purple-400 flex items-center gap-1">
                          <Building2 size={12} /> {asset.partners.name}
                        </div>
                        <div className="text-[10px] text-gray-600">
                          {asset.partners.commission_rate}% Comm
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="text-xs text-white">{asset.profiles?.full_name || 'Unknown'}</div>
                        <div className="text-[10px] text-gray-600 font-mono">{asset.profiles?.email}</div>
                      </div>
                    )}
                  </td>

                  {/* STATUS */}
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${
                      asset.status === 'active' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                      asset.status === 'scam' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                      'bg-gray-500/10 text-gray-400 border-gray-500/20'
                    }`}>
                      {asset.status === 'active' && <CheckCircle size={10} />}
                      {asset.status === 'scam' && <AlertTriangle size={10} />}
                      {asset.status}
                    </span>
                  </td>

                  {/* PRICE */}
                  <td className="p-4 font-mono text-xs">
                    {asset.currency} {asset.price?.toLocaleString()}
                  </td>

                  {/* ACTIONS */}
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                      
                      <button 
                        onClick={() => window.open(`/listing/${asset.id}`, '_blank')}
                        className="p-2 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors"
                        title="Open Public Listing Page"
                      >
                        <ExternalLink size={14} />
                      </button>

                      <button 
                        onClick={() => setEditingAsset(asset)}
                        className="p-2 hover:bg-blue-500/10 rounded text-gray-400 hover:text-blue-400 transition-colors"
                        title="Edit Asset Details"
                      >
                        <Edit size={14} />
                      </button>

                      <button 
                        onClick={() => handleStatusChange(asset.id, asset.status === 'active' ? 'draft' : 'active')}
                        className="p-2 hover:bg-yellow-500/10 rounded text-gray-400 hover:text-yellow-400 transition-colors"
                        title={asset.status === 'active' ? "Suspend Listing" : "Activate Listing"}
                      >
                        {asset.status === 'active' ? <XCircle size={14} /> : <CheckCircle size={14} />}
                      </button>

                      <button 
                        onClick={() => handleStatusChange(asset.id, 'scam')}
                        className="p-2 hover:bg-red-500/10 rounded text-gray-400 hover:text-red-500 transition-colors"
                        title="Flag as SCAM"
                      >
                        <ShieldAlert size={14} />
                      </button>

                      <button 
                        onClick={() => handleDelete(asset.id)}
                        className="p-2 hover:bg-red-900/20 rounded text-gray-600 hover:text-red-500 transition-colors border border-transparent hover:border-red-500/30"
                        title="PERMANENTLY DELETE"
                      >
                        <Trash2 size={14} />
                      </button>

                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* REUSED EDITOR MODAL */}
      {editingAsset && (
        <SubmitIntelModal 
          editingAsset={editingAsset}
          onClose={() => setEditingAsset(null)}
          onSuccess={() => {
            setEditingAsset(null);
            fetchAssets();
          }}
        />
      )}

    </div>
  );
}
