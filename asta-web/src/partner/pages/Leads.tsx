import React, { useState } from "react";
import {
  Users,
  MessageSquare,
  Clock,
  CheckCircle,
  Search,
  ArrowRight,
  Mail,
  Phone,
} from "lucide-react";

export default function Leads() {
  const [activeTab, setActiveTab] = useState<"inquiries" | "hunters">(
    "inquiries"
  );

  // MOCK DATA
  const inquiries = [
    {
      id: 1,
      name: "Kwame Mensah",
      asset: "Luxury Villa, Cantonments",
      date: "2h ago",
      status: "new",
      message: "Is this property still available for viewing this weekend?",
    },
    {
      id: 2,
      name: "Sarah Jenkins",
      asset: "2 Bed Apt, Osu",
      date: "1d ago",
      status: "responded",
      message: "Can you send more photos of the kitchen?",
    },
    {
      id: 3,
      name: "Emmanuel Ofori",
      asset: "Commercial Space, Airport",
      date: "3d ago",
      status: "closed",
      message: "We would like to make an offer.",
    },
  ];

  const hunters = [
    {
      id: 101,
      name: "Dr. A. Kwarteng",
      budget: "$450k - $600k",
      zones: ["Cantonments", "Labone"],
      match: "98%",
      avatar: "A",
    },
    {
      id: 102,
      name: "Global Corp Relocation",
      budget: "$3,000 / mo",
      zones: ["Airport Residential"],
      match: "92%",
      avatar: "G",
    },
  ];

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Users className="text-purple-500" size={24} />
          Lead Intelligence
        </h1>
        <p className="text-xs text-gray-500 font-mono uppercase tracking-widest mt-1">
          Active Opportunities & Matching Hunters
        </p>
      </div>

      {/* TABS */}
      <div className="flex border-b border-white/10">
        <button
          onClick={() => setActiveTab("inquiries")}
          className={`px-6 py-3 text-sm font-bold uppercase tracking-wider border-b-2 transition-colors ${
            activeTab === "inquiries"
              ? "border-purple-500 text-white"
              : "border-transparent text-gray-500 hover:text-gray-300"
          }`}
        >
          Direct Inquiries
        </button>
        <button
          onClick={() => setActiveTab("hunters")}
          className={`px-6 py-3 text-sm font-bold uppercase tracking-wider border-b-2 transition-colors ${
            activeTab === "hunters"
              ? "border-emerald-500 text-white"
              : "border-transparent text-gray-500 hover:text-gray-300"
          }`}
        >
          Hunter Matches
        </button>
      </div>

      {/* --- INQUIRIES TAB --- */}
      {activeTab === "inquiries" && (
        <div className="space-y-4 animate-in fade-in slide-in-from-left-4">
          {inquiries.map((lead) => (
            <div
              key={lead.id}
              className="bg-[#111] border border-white/10 p-5 rounded-xl hover:border-white/20 transition-colors flex flex-col md:flex-row gap-4"
            >
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <h3 className="text-white font-bold text-lg">{lead.name}</h3>
                  <span className="text-[10px] text-gray-500 font-mono">
                    {lead.date}
                  </span>
                </div>
                <p className="text-xs text-blue-400 font-mono mt-1 mb-2">
                  Re: {lead.asset}
                </p>
                <p className="text-gray-400 text-sm bg-white/5 p-3 rounded-lg border border-white/5">
                  "{lead.message}"
                </p>
              </div>

              <div className="flex flex-col gap-2 min-w-[140px] border-l border-white/5 pl-4 ml-2 justify-center">
                <div
                  className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded text-center mb-2 ${
                    lead.status === "new"
                      ? "bg-emerald-500/10 text-emerald-500"
                      : lead.status === "responded"
                      ? "bg-blue-500/10 text-blue-500"
                      : "bg-gray-700 text-gray-300"
                  }`}
                >
                  {lead.status}
                </div>
                <button className="flex items-center gap-2 justify-center bg-white/10 hover:bg-white/20 text-white py-2 rounded text-xs font-bold uppercase transition-colors">
                  <Mail size={12} /> Reply
                </button>
                <button className="flex items-center gap-2 justify-center bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white py-2 rounded text-xs font-bold uppercase transition-colors">
                  <Phone size={12} /> Call
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- HUNTERS TAB --- */}
      {activeTab === "hunters" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in slide-in-from-right-4">
          {hunters.map((hunter) => (
            <div
              key={hunter.id}
              className="bg-[#111] border border-white/10 p-5 rounded-xl hover:border-emerald-500/30 transition-colors group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-900/30 text-emerald-400 flex items-center justify-center font-bold border border-emerald-500/20">
                    {hunter.avatar}
                  </div>
                  <div>
                    <h3 className="text-white font-bold">{hunter.name}</h3>
                    <p className="text-xs text-gray-500">Active Search Agent</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-emerald-500">
                    {hunter.match}
                  </span>
                  <p className="text-[10px] text-gray-500 uppercase">
                    Match Score
                  </p>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm border-b border-white/5 pb-2">
                  <span className="text-gray-500">Budget Range</span>
                  <span className="text-white font-mono">{hunter.budget}</span>
                </div>
                <div className="flex justify-between text-sm border-b border-white/5 pb-2">
                  <span className="text-gray-500">Target Zones</span>
                  <span className="text-white text-right">
                    {hunter.zones.join(", ")}
                  </span>
                </div>
              </div>

              <button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors">
                Propose Asset <ArrowRight size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
