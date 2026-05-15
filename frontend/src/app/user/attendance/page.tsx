"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AttendanceCapture } from "@/components/AttendanceCapture";

export default function UserAttendancePage() {
  return (
    <ProtectedRoute role="user">
      <AttendanceCapture />
    </ProtectedRoute>
  );
}
