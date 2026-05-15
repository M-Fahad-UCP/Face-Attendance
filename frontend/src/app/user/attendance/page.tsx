"use client";

import { useCallback, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AttendanceCapture } from "@/components/AttendanceCapture";

export default function UserAttendancePage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const onMarked = useCallback(() => setRefreshKey((k) => k + 1), []);

  return (
    <ProtectedRoute role="user">
      <AttendanceCapture key={refreshKey} onMarked={onMarked} />
    </ProtectedRoute>
  );
}
