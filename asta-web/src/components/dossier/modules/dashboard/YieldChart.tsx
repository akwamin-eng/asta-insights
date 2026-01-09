import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function YieldChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) return null;

  return (
    <div style={{ width: '100%', height: '250px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
          <XAxis
            dataKey="month"
            tick={{ fill: "#666", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#666", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `K${value / 1000}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#000",
              border: "1px solid #333",
              borderRadius: "8px",
            }}
            itemStyle={{ color: "#fff", fontSize: "12px" }}
            labelStyle={{ color: "#666", fontSize: "10px", marginBottom: "4px" }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#10b981"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPrice)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
