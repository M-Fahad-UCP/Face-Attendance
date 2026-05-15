"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";

type AuditRow = {
  time_utc: string;
  category: string;
  summary: string;
  related_member: string;
};

export default function AdminAuditPage() {
  const [events, setEvents] = useState<AuditRow[]>([]);

  useEffect(() => {
    api<{ events: AuditRow[] }>("/api/audit?limit=80")
      .then((r) => setEvents(r.events))
      .catch(console.error);
  }, []);

  return (
    <ProtectedRoute role="admin">
      <h1 className="text-2xl font-bold">Audit log</h1>
      <p className="text-sm text-slate-500">Recent system activity (check-ins, admin actions, registrations).</p>
      <div className="mt-6 overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-2">Time (UTC)</th>
              <th className="p-2">Category</th>
              <th className="p-2">Summary</th>
              <th className="p-2">Member</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e, i) => (
              <tr key={i} className="border-t">
                <td className="p-2">{e.time_utc}</td>
                <td className="p-2">{e.category}</td>
                <td className="p-2">{e.summary}</td>
                <td className="p-2">{e.related_member}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!events.length && <p className="p-4 text-center text-slate-500">No events yet.</p>}
      </div>
    </ProtectedRoute>
  );
}
