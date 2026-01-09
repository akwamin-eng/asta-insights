import React, { useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import AstaMap from "./components/AstaMap";
import Dashboard from "./components/dossier/Dashboard";
import ListingPage from "./components/ListingPage";
import PublicPartnerProfile from "./pages/PublicPartnerProfile";
import AdminRouter from "./admin/AdminRouter";
import PartnerRouter from "./partner/PartnerRouter";
import { AstaAlertProvider } from "./context/AstaAlertProvider"; // 👈 FIXED: Pointing to the new Context
import { initGA, trackPageView } from "./lib/analytics";

// 🔍 THE SILENT OBSERVER
function AnalyticsTracker() {
  const location = useLocation();

  useEffect(() => {
    initGA();
  }, []);

  useEffect(() => {
    trackPageView(location.pathname + location.search);
  }, [location]);

  return null;
}

function App() {
  return (
    <AstaAlertProvider>
      {" "}
      {/* 🟢 WRAPPER: Enables Toasts Globally */}
      <Router>
        <AnalyticsTracker />
        <Routes>
          {/* The Golden State Map (Default Home) */}
          <Route path="/" element={<AstaMap />} />

          {/* The New Command Center */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* The Public Listing Page */}
          <Route path="/listing/:id" element={<ListingPage />} />

          {/* 🟢 NEW: Public Partner Agency Profile */}
          <Route path="/agency/:slug" element={<PublicPartnerProfile />} />

          {/* 🔐 ASTA TOWER (Admin Portal) */}
          <Route path="/admin/*" element={<AdminRouter />} />

          {/* 🤝 PARTNER PORTAL (New Module) */}
          {/* All routes starting with /partner/* are handed off to PartnerRouter */}
          <Route path="/partner/*" element={<PartnerRouter />} />
        </Routes>
      </Router>
    </AstaAlertProvider>
  );
}

export default App;
