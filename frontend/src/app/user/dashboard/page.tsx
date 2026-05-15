"use client";

import { useCallback, useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Card, Metric } from "@/components/ui";
import { api } from "@/lib/api";
import type { UserDashboard } from "@/lib/types";

export default function UserDashboardPage() {
  const [data, setData] = useState<UserDashboard | null>(null);

  const load = useCallback(() => {
    api<UserDashboard>("/api/dashboard/user")
      .then(setData)
      .catch(console.error);
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => {
      clearInterval(id);
      window.removeEventListener("focus", onFocus);
    };
  }, [load]);

  const statusLabel = !data?.checked_in_today
    ? "Not checked in"
    : data.checked_out_today
      ? "Checked out"
      : data.is_late
        ? "Checked in (late)"
        : "Checked in";

  return (
    <ProtectedRoute role="user">
      <h1 className="text-2xl font-bold text-slate-900">My dashboard</h1>
      {data && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <Metric label="Today's status" value={statusLabel} />
          <Metric label="Username" value={data.username} />
          {data.checked_in_today && (
            <>
              <Metric label="Check-in time" value={data.check_in_time || "—"} />
              <Metric label="Check-out time" value={data.check_out_time || "Not yet"} />
            </>
          )}
          <Card className="sm:col-span-2">
            {data.checked_in_today ? (
              <p className="text-green-700">
                You are checked in for today
                {data.is_late ? " (late arrival)." : "."}
                {!data.checked_out_today && " Remember to check out when you leave."}
              </p>
            ) : (
              <p className="text-slate-600">
                You have not marked attendance yet — open <strong>Attendance</strong> when ready.
              </p>
            )}
          </Card>
        </div>
      )}
    </ProtectedRoute>
  );
}
