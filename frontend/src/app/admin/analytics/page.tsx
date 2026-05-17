"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { WeeklyChart } from "@/components/WeeklyChart";
import { api } from "@/lib/api";

type Analytics = {
  weekly_check_ins: { date: string; check_ins: number }[];
  top_members: { username: string; check_ins: number }[];
  recent_activity: { time_utc: string; category: string; summary: string; related_member: string }[];
};

export default function AdminAnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);

  useEffect(() => {
    api<Analytics>("/api/analytics/summary").then(setData).catch(console.error);
  }, []);

  return (
    <ProtectedRoute role="admin">
      <h1 className="text-2xl font-bold">Analytics</h1>
      {data && (
        <>
          <div className="mt-6 rounded-xl border bg-white p-4">
            <WeeklyChart data={data.weekly_check_ins} />
          </div>
          {data.top_members.length > 0 && (
            <div className="mt-8">
              <h2 className="font-semibold">Top members by check-ins</h2>
              <div className="mt-2 overflow-x-auto rounded-lg border bg-white">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr className="text-left">
                      <th className="p-2">Username</th>
                      <th className="p-2">Check-ins</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_members.map((m) => (
                      <tr key={m.username} className="border-t">
                        <td className="p-2">{m.username}</td>
                        <td className="p-2">{m.check_ins}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </ProtectedRoute>
  );
}
