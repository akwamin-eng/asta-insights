import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AdminLayout from "./layouts/AdminLayout";
import AdminGuard from "./components/AdminGuard";
import AdminDashboard from "./pages/AdminDashboard";
import AssetManager from "./pages/AssetManager";
import UserManager from "./pages/UserManager";
import PartnerOps from "./pages/PartnerOps";
import PartnerManager from "./pages/PartnerManager"; // 👈 NEW IMPORT
import ReportsCenter from "./pages/ReportsCenter";

export default function AdminRouter() {
  return (
    <AdminGuard>
      <Routes>
        <Route element={<AdminLayout />}>
          {/* Default Redirect to Mission Control */}
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="assets" element={<AssetManager />} />
          <Route path="users" element={<UserManager />} />
          {/* Partner Modules */}
          <Route path="partner-ops" element={<PartnerOps />} />
          <Route path="partners" element={<PartnerManager />} />{" "}
          {/* 👈 NEW ROUTE */}
          {/* Intelligence */}
          <Route path="reports" element={<ReportsCenter />} />
          <Route
            path="*"
            element={
              <div className="p-8 text-gray-500 font-mono">
                Module Under Construction (404)
              </div>
            }
          />
        </Route>
      </Routes>
    </AdminGuard>
  );
}
