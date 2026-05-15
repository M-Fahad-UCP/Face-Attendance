"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ReportsTable } from "@/components/ReportsTable";

export default function AdminAttendancePage() {
  return (
    <ProtectedRoute role="admin">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-slate-900">Attendance</h1>
        <p className="text-sm text-slate-500">
          View check-ins for all members. Administrators cannot mark attendance — members use
          their own Attendance page.
        </p>
      </div>
      <ReportsTable defaultTodayOnly showExport={false} />
    </ProtectedRoute>
  );
}
