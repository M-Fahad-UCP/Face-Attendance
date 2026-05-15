"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Card } from "@/components/ui";
import { useAuth } from "@/lib/auth-context";

export default function UserSettingsPage() {
  const { user } = useAuth();

  return (
    <ProtectedRoute role="user">
      <h1 className="text-2xl font-bold">My profile</h1>
      <Card className="mt-6">
        <p>
          <strong>Name:</strong> {user?.full_name}
        </p>
        <p className="mt-2">
          <strong>Username:</strong> {user?.username}
        </p>
        {user?.department && (
          <p className="mt-2">
            <strong>Department:</strong> {user.department}
          </p>
        )}
      </Card>
    </ProtectedRoute>
  );
}
