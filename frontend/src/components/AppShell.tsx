"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
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
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  const renderSidebar = (idScope: "desktop" | "mobile") => (
    <>
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
        <p className="mt-2 truncate text-xs text-[var(--text-tertiary)]">
          {user?.full_name}
        </p>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-3">
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
                    layoutId={`nav-indicator-${idScope}`}
                    className="accent-gradient absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r"
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
    </>
  );

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="relative hidden w-60 shrink-0 flex-col border-r border-[var(--border)] glass lg:flex">
        {renderSidebar("desktop")}
      </aside>

      {/* Mobile drawer */}
      <div
        className={`fixed inset-0 z-40 lg:hidden ${open ? "" : "pointer-events-none"}`}
        aria-hidden={!open}
      >
        <div
          className={`absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity duration-200 ${
            open ? "opacity-100" : "opacity-0"
          }`}
          onClick={() => setOpen(false)}
        />
        <aside
          className={`absolute inset-y-0 left-0 flex w-64 max-w-[80%] flex-col border-r border-[var(--border)] glass shadow-2xl transition-transform duration-250 ease-out ${
            open ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {renderSidebar("mobile")}
        </aside>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--border)] glass px-4 py-3 lg:hidden">
          <button
            type="button"
            aria-label="Open navigation menu"
            aria-expanded={open}
            onClick={() => setOpen(true)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--border-strong)] bg-[var(--bg-surface-2)] text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <p className="text-base font-bold accent-text">FaceAttendance</p>
          <div className="w-10" aria-hidden="true" />
        </header>

        <main className="relative flex-1 overflow-x-hidden overflow-y-auto p-4 sm:p-6 lg:p-8">
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
        </main>
      </div>
    </div>
  );
}
