"use client";

import Link from "next/link";
import { useState } from "react";
import { z } from "zod";
import { api } from "@/lib/api";
import { Button, Card, Input, Label } from "@/components/ui";

const step1Schema = z
  .object({
    full_name: z.string().min(1, "Full name required"),
    username: z
      .string()
      .regex(/^[A-Za-z0-9_.-]{3,32}$/, "Username: 3–32 chars, letters, digits, ._-"),
    password: z.string().min(6, "Password at least 6 characters"),
    confirm: z.string(),
  })
  .refine((d) => d.password === d.confirm, { message: "Passwords must match", path: ["confirm"] });

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  function nextStep1(e: React.FormEvent) {
    e.preventDefault();
    const parsed = step1Schema.safeParse({
      full_name: fullName,
      username,
      password,
      confirm,
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || "Invalid");
      return;
    }
    setError("");
    setStep(2);
  }

  async function submitSignup() {
    if (!files.length) {
      setError("Upload at least one face photo.");
      return;
    }
    setLoading(true);
    setError("");
    const fd = new FormData();
    fd.append("full_name", fullName);
    fd.append("username", username);
    fd.append("password", password);
    files.slice(0, 5).forEach((f) => fd.append("images", f));
    try {
      await api("/api/auth/signup", { method: "POST", formData: fd });
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <Card className="max-w-md text-center">
          <p className="text-lg font-semibold text-green-700">Account created</p>
          <p className="mt-2 text-sm text-slate-600">You can sign in now.</p>
          <Link href="/login" className="mt-4 inline-block text-indigo-600 hover:underline">
            Go to sign in
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-lg">
        <p className="text-sm text-slate-500">Step {step} of 2</p>
        <h1 className="text-xl font-bold text-slate-900">Create member account</h1>
        {step === 1 && (
          <form onSubmit={nextStep1} className="mt-4 space-y-3">
            <div>
              <Label>Full name</Label>
              <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div>
              <Label>Username</Label>
              <Input value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div>
              <Label>Password</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div>
              <Label>Confirm password</Label>
              <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full">
              Continue
            </Button>
          </form>
        )}
        {step === 2 && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-slate-600">
              Upload 1–5 clear, front-facing photos for face enrollment.
            </p>
            <input
              type="file"
              accept="image/png,image/jpeg"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
            />
            <p className="text-xs text-slate-500">{files.length} file(s) selected</p>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button onClick={submitSignup} disabled={loading} className="flex-1">
                {loading ? "Creating…" : "Create account"}
              </Button>
            </div>
          </div>
        )}
        <p className="mt-4 text-center text-sm">
          <Link href="/login" className="text-indigo-600 hover:underline">
            Back to sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
