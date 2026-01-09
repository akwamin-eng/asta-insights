import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X, CheckCircle, AlertTriangle, Info } from 'lucide-react';

// --- Types ---
type AlertType = 'success' | 'error' | 'warning' | 'info';

interface Alert {
  id: string;
  message: string;
  type: AlertType;
}

interface AstaAlertContextType {
  showAlert: (message: string, type?: AlertType, duration?: number) => void;
}

// --- Context ---
const AstaAlertContext = createContext<AstaAlertContextType | undefined>(undefined);

// --- Provider Component ---
export const AstaAlertProvider = ({ children }: { children: ReactNode }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const showAlert = useCallback((message: string, type: AlertType = 'info', duration = 4000) => {
    const id = Math.random().toString(36).substring(7);
    const newAlert = { id, message, type };
    
    setAlerts((prev) => [...prev, newAlert]);

    // Auto dismiss
    setTimeout(() => {
      setAlerts((prev) => prev.filter((alert) => alert.id !== id));
    }, duration);
  }, []);

  const removeAlert = (id: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  };

  return (
    <AstaAlertContext.Provider value={{ showAlert }}>
      {children}
      
      {/* Toast Container - Fixed to top center */}
      <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[9999] flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {alerts.map((alert) => (
            <AlertItem key={alert.id} alert={alert} onDismiss={() => removeAlert(alert.id)} />
          ))}
        </AnimatePresence>
      </div>
    </AstaAlertContext.Provider>
  );
};

// --- Hook ---
export const useAstaAlert = () => {
  const context = useContext(AstaAlertContext);
  if (!context) {
    throw new Error('useAstaAlert must be used within an AstaAlertProvider');
  }
  return context;
};

// --- Sub-Component: The Individual Toast ---
const AlertItem = ({ alert, onDismiss }: { alert: Alert; onDismiss: () => void }) => {
  const styles = {
    success: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-100',
    error: 'bg-red-500/10 border-red-500/20 text-red-100',
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-100',
    info: 'bg-blue-500/10 border-blue-500/20 text-blue-100',
  };

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-emerald-400" />,
    error: <X className="w-5 h-5 text-red-400" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-400" />,
    info: <Info className="w-5 h-5 text-blue-400" />,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.9 }}
      layout
      className={`pointer-events-auto backdrop-blur-md border rounded-xl px-4 py-3 shadow-2xl flex items-center gap-3 min-w-[300px] max-w-md ${styles[alert.type]}`}
    >
      {icons[alert.type]}
      <span className="text-sm font-medium flex-1">{alert.message}</span>
      <button onClick={onDismiss} className="opacity-60 hover:opacity-100 transition-opacity">
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
};
