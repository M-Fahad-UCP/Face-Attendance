"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { WeeklyChart } from "@/components/WeeklyChart";
import { Metric } from "@/components/ui";
import { api } from "@/lib/api";

type TodayRow = {
  username: string;
  full_name: string;
  check_in_time: string;
  check_out_time: string;
  checked_out: boolean;
};

type AdminDash = {
  total_members: number;
  present_today: number;
  absent_estimate: number;
  avg_match_confidence: number | null;
  weekly_check_ins: { date: string; check_ins: number }[];
  today_attendance: TodayRow[];
  recent_activity: { time_utc: string; category: string; summary: string; related_member: string }[];
};

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDash | null>(null);

  const load = () => {
    api<AdminDash>("/api/dashboard/admin").then(setData).catch(console.error);
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => {
      clearInterval(id);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  return (
    <ProtectedRoute role="admin">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
      <p className="text-sm text-slate-500">Operational overview</p>
      {data && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Total members" value={data.total_members} />
            <Metric label="Present today" value={data.present_today} />
            <Metric label="Absent (est.)" value={data.absent_estimate} />
            <Metric
              label="Avg. match confidence"
              value={
                data.avg_match_confidence != null
                  ? `${(data.avg_match_confidence * 100).toFixed(1)}%`
                  : "—"
              }
            />
          </div>
          <div className="mt-8">
            <h2 className="font-semibold">Today&apos;s attendance</h2>
            <p className="mt-1 text-sm text-slate-500">
              Check-out time is recorded when a member signs out.
            </p>
            <div className="mt-2 overflow-x-auto rounded-lg border bg-white">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="p-2">Member</th>
                    <th className="p-2">Check-in</th>
                    <th className="p-2">Check-out</th>
                    <th className="p-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.today_attendance ?? []).map((r) => (
                    <tr key={r.username} className="border-t">
                      <td className="p-2">{r.full_name}</td>
                      <td className="p-2">{r.check_in_time || "—"}</td>
                      <td className="p-2">{r.check_out_time || "—"}</td>
                      <td className="p-2">
                        {r.checked_out ? "Checked out" : "Still in"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!(data.today_attendance ?? []).length && (
                <p className="p-4 text-center text-slate-500">No check-ins yet today.</p>
              )}
            </div>
          </div>
          <div className="mt-8 rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-4 font-semibold">Daily check-ins (14 days)</h2>
            <WeeklyChart data={data.weekly_check_ins} />
          </div>
          <div className="mt-8">
            <h2 className="font-semibold">Recent activity</h2>
            <div className="mt-2 overflow-x-auto rounded-lg border">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="p-2">Time</th>
                    <th className="p-2">Category</th>
                    <th className="p-2">Summary</th>
                    <th className="p-2">Member</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_activity.map((e, i) => (
                    <tr key={i} className="border-t">
                      <td className="p-2">{e.time_utc}</td>
                      <td className="p-2">{e.category}</td>
                      <td className="p-2">{e.summary}</td>
                      <td className="p-2">{e.related_member}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </ProtectedRoute>
  );
}
