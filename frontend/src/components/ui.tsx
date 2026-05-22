"use client";

import { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";

/* ---------------- Card ---------------- */
type CardProps = {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
} & Omit<HTMLMotionProps<"div">, "children" | "className">;

export function Card({
  children,
  className = "",
  interactive = false,
  ...rest
}: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={`surface-card ${interactive ? "surface-card-hover" : ""} rounded-2xl p-6 ${className}`}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

/* ---------------- Button ---------------- */
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  loading?: boolean;
};

export function Button({
  className = "",
  variant = "primary",
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const base =
    "group relative inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium " +
    "transition-all duration-150 ease-out " +
    "active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 " +
    "focus:outline-none";

  const variants: Record<string, string> = {
    primary:
      "text-white accent-gradient shadow-[0_8px_24px_-8px_rgba(99,102,241,0.55)] " +
      "hover:shadow-[0_12px_32px_-8px_rgba(99,102,241,0.7)] hover:brightness-110 " +
      "border border-white/10",
    secondary:
      "text-[var(--text-primary)] bg-[var(--bg-surface-2)] " +
      "hover:bg-[var(--bg-surface-hover)] border border-[var(--border-strong)] " +
      "hover:border-[var(--accent)]",
    danger:
      "text-white bg-gradient-to-br from-rose-500 to-red-600 " +
      "hover:brightness-110 border border-white/10 " +
      "shadow-[0_8px_24px_-8px_rgba(244,63,94,0.55)]",
    ghost:
      "text-[var(--text-secondary)] hover:text-[var(--text-primary)] " +
      "hover:bg-[var(--bg-surface-hover)] border border-transparent",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="spinner-ring" aria-hidden />}
      <span className="relative">{children}</span>
    </button>
  );
}

/* ---------------- Input ---------------- */
export function Input({
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={
        "w-full rounded-lg border border-[var(--border-strong)] bg-[var(--bg-surface-2)] " +
        "px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] " +
        "transition-colors duration-150 " +
        "focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-ring)] " +
        "hover:border-[var(--border-strong)] " +
        `${className}`
      }
      {...props}
    />
  );
}

/* ---------------- Label ---------------- */
export function Label({ children }: { children: ReactNode }) {
  return (
    <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--text-tertiary)]">
      {children}
    </label>
  );
}

/* ---------------- Metric ---------------- */
export function Metric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -2 }}
      className="surface-card surface-card-hover relative overflow-hidden rounded-2xl p-5"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full opacity-30 blur-2xl"
        style={{ background: "radial-gradient(circle, var(--accent) 0%, transparent 70%)" }}
      />
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--text-tertiary)]">
        {label}
      </p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-[var(--text-primary)]">
        {value}
      </p>
    </motion.div>
  );
}

/* ---------------- Skeleton ---------------- */
export function Skeleton({
  className = "",
}: {
  className?: string;
}) {
  return <div className={`shimmer rounded-lg ${className}`} />;
}

/* ---------------- Spinner ---------------- */
export function Spinner({ className = "" }: { className?: string }) {
  return <span className={`spinner-ring ${className}`} aria-label="Loading" />;
}

/* ---------------- Badge ---------------- */
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "good" | "warn" | "bad" | "brand";
}) {
  const tones: Record<string, string> = {
    neutral: "bg-[var(--bg-surface-hover)] text-[var(--text-secondary)] border-[var(--border)]",
    good: "bg-[var(--success-surface)] text-[var(--success)] border-[rgba(52,211,153,0.3)]",
    warn: "bg-[var(--warning-surface)] text-[var(--warning)] border-[rgba(251,191,36,0.3)]",
    bad: "bg-[var(--danger-surface)] text-[var(--danger)] border-[rgba(248,113,113,0.3)]",
    brand: "bg-[var(--accent-soft)] text-[#a5b4fc] border-[rgba(99,102,241,0.3)]",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
