import { Routes, Route, Navigate } from "react-router-dom";
import PartnerLayout from "./layouts/PartnerLayout";
import PartnerDashboard from "./pages/Dashboard"; // Ensure this matches your filename (might be PartnerDashboard.jsx)
import PartnerSettings from "./pages/Settings";
import MyAssets from "./pages/MyAssets"; // 👈 NEW
import Leads from "./pages/Leads"; // 👈 NEW

export default function PartnerRouter() {
  return (
    <Routes>
      <Route element={<PartnerLayout />}>
        {/* Dashboard */}
        <Route index element={<PartnerDashboard />} />

        {/* Core Modules */}
        <Route path="listings" element={<MyAssets />} />
        <Route path="leads" element={<Leads />} />
        <Route path="settings" element={<PartnerSettings />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/partner" replace />} />
      </Route>
    </Routes>
  );
}
