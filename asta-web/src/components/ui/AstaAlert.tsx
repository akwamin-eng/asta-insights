import React, { createContext, useContext, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  X,
  Terminal,
} from "lucide-react";

// --- TYPES ---
type AlertType = "success" | "error" | "warning" | "info";

interface Alert {
  id: string;
  type: AlertType;
  title: string;
  message?: string;
}

interface AlertContextType {
  toast: (type: AlertType, title: string, message?: string) => void;
}

const AlertContext = createContext<AlertContextType | undefined>(undefined);

// --- HOOK ---
export const useAstaAlert = () => {
  const context = useContext(AlertContext);
  if (!context)
    throw new Error("useAstaAlert must be used within an AlertProvider");
  return context;
};

// --- COMPONENT ---
export const AstaAlertProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const toast = useCallback(
    (type: AlertType, title: string, message?: string) => {
      const id = Math.random().toString(36).substring(7);
      setAlerts((prev) => [...prev, { id, type, title, message }]);

      // Auto-dismiss logic
      setTimeout(() => {
        setAlerts((prev) => prev.filter((a) => a.id !== id));
      }, 5000);
    },
    []
  );

  const removeAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  // Icon Mapping
  const icons = {
    success: <CheckCircle2 className="text-emerald-500" size={20} />,
    error: <XCircle className="text-red-500" size={20} />,
    warning: <AlertTriangle className="text-amber-500" size={20} />,
    info: <Info className="text-blue-500" size={20} />,
  };

  // Color Mapping (Borders & Accents)
  const colors = {
    success:
      "border-emerald-500/50 bg-emerald-950/90 shadow-[0_0_15px_rgba(16,185,129,0.2)]",
    error:
      "border-red-500/50 bg-red-950/90 shadow-[0_0_15px_rgba(239,68,68,0.2)]",
    warning:
      "border-amber-500/50 bg-amber-950/90 shadow-[0_0_15px_rgba(245,158,11,0.2)]",
    info: "border-blue-500/50 bg-blue-950/90 shadow-[0_0_15px_rgba(59,130,246,0.2)]",
  };

  return (
    <AlertContext.Provider value={{ toast }}>
      {children}

      {/* ALERT CONTAINER */}
      <div className="fixed top-20 right-4 z-[200] flex flex-col gap-3 w-full max-w-sm pointer-events-none">
        <AnimatePresence>
          {alerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: 50, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.95 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={`pointer-events-auto relative overflow-hidden rounded-lg border backdrop-blur-md p-4 flex items-start gap-3 ${
                colors[alert.type]
              }`}
            >
              {/* Scanline Effect */}
              <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />

              <div className="shrink-0 mt-0.5">{icons[alert.type]}</div>

              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  {alert.title}
                </h4>
                {alert.message && (
                  <p className="text-xs text-gray-300 font-mono mt-1 leading-relaxed opacity-90">
                    {alert.message}
                  </p>
                )}
              </div>

              <button
                onClick={() => removeAlert(alert.id)}
                className="text-white/40 hover:text-white transition-colors shrink-0"
              >
                <X size={16} />
              </button>

              {/* Progress Bar (Visual Timer) */}
              <motion.div
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: 5, ease: "linear" }}
                className="absolute bottom-0 left-0 h-0.5 bg-white/20"
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </AlertContext.Provider>
  );
};
