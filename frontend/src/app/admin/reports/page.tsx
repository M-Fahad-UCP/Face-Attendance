"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ReportsTable } from "@/components/ReportsTable";

export default function AdminReportsPage() {
  return (
    <ProtectedRoute role="admin">
      <ReportsTable />
    </ProtectedRoute>
  );
}
