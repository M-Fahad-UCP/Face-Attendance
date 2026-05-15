"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ReportsTable } from "@/components/ReportsTable";

export default function UserReportsPage() {
  return (
    <ProtectedRoute role="user">
      <ReportsTable />
    </ProtectedRoute>
  );
}
