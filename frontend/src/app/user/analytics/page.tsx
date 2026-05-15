"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { WeeklyChart } from "@/components/WeeklyChart";
import { api } from "@/lib/api";

type Analytics = {
  weekly_check_ins: { date: string; check_ins: number }[];
};

export default function UserAnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);

  useEffect(() => {
    api<Analytics>("/api/analytics/summary").then(setData).catch(console.error);
  }, []);

  return (
    <ProtectedRoute role="user">
      <h1 className="text-2xl font-bold">Analytics</h1>
      <p className="text-sm text-slate-500">Your attendance trends</p>
      {data && (
        <div className="mt-6 rounded-xl border bg-white p-4">
          <WeeklyChart data={data.weekly_check_ins} />
        </div>
      )}
    </ProtectedRoute>
  );
}
