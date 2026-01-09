import { motion } from "framer-motion";
import React from "react";

export const PageReveal = ({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.99 }} // Subtle start
      animate={{ opacity: 1, y: 0, scale: 1 }} // Snap to position
      exit={{ opacity: 0, y: -10, scale: 0.99 }} // Clean exit
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
        mass: 0.5,
      }}
      className={`w-full h-full ${className}`}
    >
      {children}
    </motion.div>
  );
};
