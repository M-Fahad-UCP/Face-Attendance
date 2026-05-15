"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import { Button, Card, Input, Label } from "@/components/ui";

export default function AdminSettingsPage() {
  const [threshold, setThreshold] = useState(0.45);
  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [logs, setLogs] = useState("");
  const [msg, setMsg] = useState("");
  const [resetAck, setResetAck] = useState(false);

  useEffect(() => {
    api<{ recognition_threshold: number }>("/api/settings").then((s) =>
      setThreshold(s.recognition_threshold)
    );
    api<{ logs: string }>("/api/settings/logs").then((r) => setLogs(r.logs)).catch(() => {});
  }, []);

  async function saveThreshold() {
    try {
      const res = await api<{ recognition_threshold: number }>("/api/settings/threshold", {
        method: "PATCH",
        json: { recognition_threshold: threshold },
      });
      setThreshold(res.recognition_threshold);
      setMsg("Threshold saved.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPw !== newPw2) {
      setMsg("Passwords do not match.");
      return;
    }
    try {
      await api("/api/settings/password", {
        method: "POST",
        json: { current_password: curPw, new_password: newPw },
      });
      setMsg("Password updated.");
      setCurPw("");
      setNewPw("");
      setNewPw2("");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    }
  }

  async function resetAttendance() {
    if (!resetAck) return;
    try {
      await api("/api/attendance/reset", { method: "POST" });
      setMsg("Attendance log cleared.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    }
  }

  return (
    <ProtectedRoute role="admin">
      <h1 className="text-2xl font-bold">Settings</h1>
      {msg && <p className="mt-2 text-sm text-indigo-600">{msg}</p>}
      <Card className="mt-6">
        <h2 className="font-semibold">Recognition threshold</h2>
        <p className="text-sm text-slate-500">Higher = stricter matches (cosine similarity)</p>
        <input
          type="range"
          min={0.2}
          max={0.8}
          step={0.01}
          value={threshold}
          onChange={(e) => setThreshold(parseFloat(e.target.value))}
          className="mt-3 w-full"
        />
        <p className="text-sm">{threshold.toFixed(2)}</p>
        <Button className="mt-2" onClick={saveThreshold}>
          Save threshold
        </Button>
      </Card>
      <Card className="mt-6">
        <h2 className="font-semibold">Administrator password</h2>
        <form onSubmit={changePassword} className="mt-3 space-y-3 max-w-md">
          <div>
            <Label>Current password</Label>
            <Input type="password" value={curPw} onChange={(e) => setCurPw(e.target.value)} />
          </div>
          <div>
            <Label>New password</Label>
            <Input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
          </div>
          <div>
            <Label>Confirm new password</Label>
            <Input type="password" value={newPw2} onChange={(e) => setNewPw2(e.target.value)} />
          </div>
          <Button type="submit">Update password</Button>
        </form>
      </Card>
      <Card className="mt-6">
        <h2 className="font-semibold">Attendance data</h2>
        <label className="mt-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={resetAck} onChange={(e) => setResetAck(e.target.checked)} />
          I understand this permanently deletes attendance rows
        </label>
        <Button className="mt-3" variant="danger" onClick={resetAttendance} disabled={!resetAck}>
          Reset attendance CSV
        </Button>
      </Card>
      <Card className="mt-6">
        <h2 className="font-semibold">System logs (tail)</h2>
        <pre className="mt-2 max-h-64 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
          {logs}
        </pre>
      </Card>
    </ProtectedRoute>
  );
}
