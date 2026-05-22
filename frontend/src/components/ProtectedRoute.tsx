"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppShell } from "./AppShell";
import { Spinner } from "./ui";

export function ProtectedRoute({
  children,
  role,
}: {
  children: React.ReactNode;
  role?: "admin" | "user";
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (role && user.role !== role) {
      router.replace(user.role === "admin" ? "/admin/dashboard" : "/user/dashboard");
    }
  }, [user, loading, role, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 text-[var(--text-tertiary)]">
        <Spinner className="!h-6 !w-6 text-[var(--accent)]" />
        <p className="text-sm">Loading…</p>
      </div>
    );
  }
  if (role && user.role !== role) return null;

  return <AppShell>{children}</AppShell>;
}
