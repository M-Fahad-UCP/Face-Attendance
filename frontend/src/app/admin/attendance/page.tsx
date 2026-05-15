"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AttendanceCapture } from "@/components/AttendanceCapture";

export default function AdminAttendancePage() {
  return (
    <ProtectedRoute role="admin">
      <AttendanceCapture />
    </ProtectedRoute>
  );
}
