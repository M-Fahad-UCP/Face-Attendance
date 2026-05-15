"use client";

import { useCallback, useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Card, Metric } from "@/components/ui";
import { api } from "@/lib/api";

type UserDash = {
  username: string;
  full_name: string;
  checked_in_today: boolean;
};

export default function UserDashboardPage() {
  const [data, setData] = useState<UserDash | null>(null);

  const load = useCallback(() => {
    api<UserDash>("/api/dashboard/user")
      .then(setData)
      .catch(console.error);
  }, []);

  useEffect(() => {
    load();
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [load]);

  return (
    <ProtectedRoute role="user">
      <h1 className="text-2xl font-bold text-slate-900">My dashboard</h1>
      {data && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <Metric
            label="Today's status"
            value={data.checked_in_today ? "Checked in" : "Not checked in"}
          />
          <Metric label="Username" value={data.username} />
          <Card className="sm:col-span-2">
            {data.checked_in_today ? (
              <p className="text-green-700">You are checked in for today.</p>
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
