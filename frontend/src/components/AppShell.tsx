"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { Button } from "./ui";

const ADMIN_NAV = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/admin/attendance", label: "View attendance" },
  { href: "/admin/members", label: "Members" },
  { href: "/admin/reports", label: "Reports" },
  { href: "/admin/analytics", label: "Analytics" },
  { href: "/admin/audit", label: "Audit log" },
  { href: "/admin/settings", label: "Settings" },
];

const USER_NAV = [
  { href: "/user/dashboard", label: "Dashboard" },
  { href: "/user/attendance", label: "Attendance" },
  { href: "/user/reports", label: "Reports" },
  { href: "/user/analytics", label: "Analytics" },
  { href: "/user/settings", label: "Settings" },
];

const PAGE_TRANSITION = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: { duration: 0.28, ease: [0.22, 1, 0.36, 1] as const },
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const nav = user?.role === "admin" ? ADMIN_NAV : USER_NAV;

  return (
    <div className="flex min-h-screen">
      <aside className="relative flex w-60 flex-col border-r border-[var(--border)] glass">
        <div className="px-5 py-6">
          <div className="flex items-center gap-2">
            <span
              aria-hidden
              className="accent-gradient inline-flex h-8 w-8 items-center justify-center rounded-lg text-white shadow-[0_8px_24px_-8px_rgba(99,102,241,0.6)]"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
                <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0 2c-3.3 0-9 1.7-9 5v3h18v-3c0-3.3-5.7-5-9-5Z" />
              </svg>
            </span>
            <p className="text-lg font-bold accent-text">FaceAttendance</p>
          </div>
          <p className="mt-2 text-xs text-[var(--text-tertiary)] truncate">
            {user?.full_name}
          </p>
        </div>

        <nav className="flex-1 space-y-1 px-3 pb-3">
          {nav.map((item, i) => {
            const active = pathname === item.href;
            return (
              <motion.div
                key={item.href}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.04 * i, duration: 0.25, ease: "easeOut" }}
              >
                <Link
                  href={item.href}
                  className={`group relative flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150 ${
                    active
                      ? "bg-[var(--accent-soft)] text-[#c7d2fe] shadow-[inset_0_0_0_1px_rgba(99,102,241,0.25)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-indicator"
                      className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r accent-gradient"
                      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                    />
                  )}
                  <span className="ml-1">{item.label}</span>
                </Link>
              </motion.div>
            );
          })}
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          <Button variant="secondary" className="w-full" onClick={() => logout()}>
            Sign out
          </Button>
        </div>
      </aside>

      <main className="relative flex-1 overflow-auto">
        <div className="px-8 py-8">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={pathname}
              initial={PAGE_TRANSITION.initial}
              animate={PAGE_TRANSITION.animate}
              exit={PAGE_TRANSITION.exit}
              transition={PAGE_TRANSITION.transition}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
