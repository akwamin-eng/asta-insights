import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 🛡️ PRODUCTION LOG FILTERING
// This suppresses specific 3rd-party deprecation warnings to keep the console clean for development.
const originalWarn = console.warn;
const originalError = console.error;

console.warn = (...args) => {
  const msg = args[0];
  if (typeof msg === 'string' && (
    msg.includes('google.maps.places') || 
    msg.includes('As of March 1st, 2025')
  )) {
    return;
  }
  originalWarn(...args);
};

console.error = (...args) => {
  const msg = args[0];
  if (typeof msg === 'string' && (
    msg.includes('defaultProps') || 
    msg.includes('GoTrueClient')
  )) {
    return;
  }
  originalError(...args);
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
