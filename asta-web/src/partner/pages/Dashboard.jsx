import React from "react";

const PartnerDashboard = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Partner Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Simple Stat Card 1 */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-gray-500 text-sm">Active Leads</h3>
          <p className="text-3xl font-bold text-blue-600">12</p>
        </div>
        {/* Simple Stat Card 2 */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-gray-500 text-sm">Pending Deals</h3>
          <p className="text-3xl font-bold text-orange-500">5</p>
        </div>
        {/* Simple Stat Card 3 */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-gray-500 text-sm">Total Revenue</h3>
          <p className="text-3xl font-bold text-green-600">$12,450</p>
        </div>
      </div>
    </div>
  );
};

export default PartnerDashboard;
