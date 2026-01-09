import React from "react";
import { Activity, Users, DollarSign, ArrowUpRight } from "lucide-react";

const PartnerDashboard = () => {
  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Mission Control
        </h1>
        <p className="text-xs text-gray-500 font-mono uppercase tracking-widest mt-1">
          Live Metrics // Partner Node
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Active Assets"
          value="12"
          trend="+2 this week"
          icon={<Activity className="text-emerald-500" size={20} />}
        />
        <StatCard
          title="Pending Deals"
          value="5"
          trend="Action Required"
          isWarning
          icon={<Users className="text-orange-500" size={20} />}
        />
        <StatCard
          title="Total Revenue"
          value="$12,450"
          trend="+12% vs last month"
          icon={<DollarSign className="text-blue-500" size={20} />}
        />
      </div>

      {/* Recent Activity Section */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-6">
        <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Activity size={16} className="text-emerald-500" />
          Recent Signals
        </h3>

        <div className="space-y-4">
          {/* Mock Activity Item 1 */}
          <div className="flex items-start gap-4 p-4 border border-white/5 rounded-lg bg-white/5 hover:border-emerald-500/30 transition-colors group">
            <div className="mt-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            </div>
            <div>
              <p className="text-sm text-gray-200 font-medium group-hover:text-emerald-400 transition-colors">
                New Inquiry on "The Osu Penthouse"
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Potential tenant requested a viewing for tomorrow at 2:00 PM.
              </p>
            </div>
            <span className="ml-auto text-[10px] font-mono text-gray-600">
              2h ago
            </span>
          </div>

          {/* Mock Activity Item 2 */}
          <div className="flex items-start gap-4 p-4 border border-white/5 rounded-lg bg-white/5 hover:border-emerald-500/30 transition-colors group">
            <div className="mt-1">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            </div>
            <div>
              <p className="text-sm text-gray-200 font-medium group-hover:text-blue-400 transition-colors">
                Listing Verified: Cantonments Villa
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Asta Scouts have confirmed the property details. Trust Score
                updated to 98%.
              </p>
            </div>
            <span className="ml-auto text-[10px] font-mono text-gray-600">
              5h ago
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Reusable Dark Stat Card Component
const StatCard = ({ title, value, trend, icon, isWarning }: any) => (
  <div className="bg-[#111] border border-white/10 p-6 rounded-xl hover:border-white/20 transition-all group">
    <div className="flex justify-between items-start mb-4">
      <div className="p-2 bg-white/5 rounded-lg border border-white/5 group-hover:border-white/10 transition-colors">
        {icon}
      </div>
      <ArrowUpRight
        size={16}
        className="text-gray-600 group-hover:text-white transition-colors"
      />
    </div>
    <h3 className="text-xs font-mono text-gray-500 uppercase tracking-widest">
      {title}
    </h3>
    <p className="text-3xl font-bold text-white mt-1 tracking-tight">{value}</p>
    <p
      className={`text-xs mt-2 font-medium ${
        isWarning ? "text-orange-400" : "text-emerald-400"
      }`}
    >
      {trend}
    </p>
  </div>
);

export default PartnerDashboard;
