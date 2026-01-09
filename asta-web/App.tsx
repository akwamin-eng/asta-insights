import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AstaMap from './components/AstaMap';
import Dashboard from './components/dossier/Dashboard';

function App() {
  return (
    <Router>
      <Routes>
        {/* The Golden State Map (Default Home) */}
        <Route path="/" element={<AstaMap />} />
        
        {/* The New Command Center */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* 🆕 NEW: The Public Listing Route (Traffic Destination) */}
        {/* Currently reusing AstaMap, but this URL structure /listing/123 is now valid */}
        <Route path="/listing/:id" element={<AstaMap />} />
      </Routes>
    </Router>
  );
}

export default App;
