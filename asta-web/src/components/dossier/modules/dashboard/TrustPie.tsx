import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

export default function TrustPie({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-full min-h-[200px] flex items-center justify-center text-gray-500 text-xs font-mono uppercase tracking-widest">
        No Intel Data
      </div>
    );
  }

  // Calculate percentage safely
  const total = data.reduce((acc, curr) => acc + curr.value, 0);
  const percentage = total > 0 ? Math.round((data[0].value / total) * 100) : 0;

  return (
    <div className="w-full h-full min-h-[220px] relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          {/* 🟢 DEFS: Gradients & Shadows for Premium 3D Look */}
          <defs>
            <filter id="shadow3d" x="-20%" y="-20%" width="140%" height="145%">
              <feDropShadow dx="0" dy="4" stdDeviation="4" floodOpacity="0.3" />
            </filter>
            {data.map((entry, index) => (
              <linearGradient key={`grad-${index}`} id={`grad-${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                <stop offset="100%" stopColor={entry.color} stopOpacity={0.6} />
              </linearGradient>
            ))}
          </defs>

          {/* 🌑 3D EXTRUSION LAYER (Darker base behind the main pie) */}
          {/* Moved cy to 45% to shift up */}
          <Pie
            data={data}
            cx="50%"
            cy="45%" 
            innerRadius="60%"
            outerRadius="77%"
            startAngle={90}
            endAngle={-270}
            paddingAngle={0}
            dataKey="value"
            stroke="none"
            isAnimationActive={false} 
          >
            {data.map((entry, index) => (
              <Cell key={`shadow-cell-${index}`} fill={entry.color} fillOpacity={0.2} />
            ))}
          </Pie>

          {/* ☀️ MAIN GLOSSY LAYER */}
          {/* Moved cy to 45% to shift up, reduced radius slightly */}
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            innerRadius="65%"
            outerRadius="82%"
            startAngle={90}
            endAngle={-270}
            paddingAngle={4}
            dataKey="value"
            stroke="none"
            filter="url(#shadow3d)"
            cornerRadius={4}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={`url(#grad-${index})`} 
                stroke="rgba(255,255,255,0.1)"
                strokeWidth={1}
              />
            ))}
          </Pie>

          <Tooltip
            cursor={false}
            contentStyle={{
              backgroundColor: "rgba(0,0,0,0.9)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              backdropFilter: "blur(4px)",
              boxShadow: "0 10px 30px rgba(0,0,0,0.5)"
            }}
            itemStyle={{ color: "#fff", fontSize: "12px", fontFamily: "monospace" }}
          />
        </PieChart>
      </ResponsiveContainer>
      
      {/* 🎯 CENTER DATA OVERLAY */}
      {/* Added pb-8 to shift center text up to match the new pie position */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none pb-8">
        <div className="text-center flex flex-col items-center">
          <div className="relative">
            <span className="block text-3xl font-black text-white tracking-tighter drop-shadow-lg">
              {percentage}%
            </span>
            {/* Glow effect behind text */}
            <div className="absolute -inset-4 bg-emerald-500/20 blur-xl rounded-full -z-10 animate-pulse" />
          </div>
          <span className="text-[10px] text-gray-400 font-mono uppercase tracking-[0.2em] mt-1">
            Trust Score
          </span>
        </div>
      </div>
    </div>
  );
}
