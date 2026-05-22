"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function WeeklyChart({
  data,
}: {
  data: { date: string; check_ins: number }[];
}) {
  if (!data.length) {
    return (
      <p className="text-sm text-[var(--text-tertiary)]">
        No attendance history yet.
      </p>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="barFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.95} />
            <stop offset="100%" stopColor="#6366f1" stopOpacity={0.6} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#8a8a9c" }}
          axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
          tickLine={{ stroke: "rgba(255,255,255,0.08)" }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: "#8a8a9c" }}
          axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
          tickLine={{ stroke: "rgba(255,255,255,0.08)" }}
        />
        <Tooltip
          contentStyle={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-strong)",
            borderRadius: 10,
            color: "var(--text-primary)",
            boxShadow: "0 12px 32px -12px rgba(0,0,0,0.6)",
          }}
          labelStyle={{ color: "var(--text-tertiary)", fontSize: 12 }}
          cursor={{ fill: "rgba(99,102,241,0.08)" }}
        />
        <Bar
          dataKey="check_ins"
          fill="url(#barFill)"
          radius={[6, 6, 0, 0]}
          animationDuration={600}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
