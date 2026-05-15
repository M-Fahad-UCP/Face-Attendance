"use client";

import { useCallback, useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import type { Member } from "@/lib/types";
import { Button, Card, Input, Label } from "@/components/ui";

export default function AdminMembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [search, setSearch] = useState("");
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [department, setDepartment] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [msg, setMsg] = useState("");
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);

  const load = useCallback(() => {
    api<Member[]>("/api/users").then(setMembers).catch(console.error);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = members.filter(
    (m) =>
      !search.trim() ||
      m.username.toLowerCase().includes(search.toLowerCase()) ||
      m.full_name.toLowerCase().includes(search.toLowerCase()) ||
      (m.department || "").toLowerCase().includes(search.toLowerCase())
  );

  async function createMember(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    const fd = new FormData();
    fd.append("full_name", fullName);
    fd.append("username", username);
    fd.append("password", password);
    fd.append("department", department);
    files.slice(0, 5).forEach((f) => fd.append("images", f));
    try {
      await api("/api/users", { method: "POST", formData: fd });
      setMsg("Member created.");
      setFullName("");
      setUsername("");
      setPassword("");
      setDepartment("");
      setFiles([]);
      load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Failed");
    }
  }

  async function deleteMember(name: string) {
    try {
      await api(`/api/users/${encodeURIComponent(name)}`, { method: "DELETE" });
      setPendingDelete(null);
      load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <ProtectedRoute role="admin">
      <h1 className="text-2xl font-bold">Members</h1>
      <Card className="mt-6">
        <h2 className="font-semibold">Register a new member</h2>
        <form onSubmit={createMember} className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <Label>Full name</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div>
            <Label>Username</Label>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div>
            <Label>Password</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div>
            <Label>Department</Label>
            <Input value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label>Face images</Label>
            <input
              type="file"
              accept="image/png,image/jpeg"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
            />
          </div>
          <Button type="submit">Create member + face template</Button>
        </form>
        {msg && <p className="mt-2 text-sm text-slate-600">{msg}</p>}
      </Card>
      <div className="mt-8">
        <Input
          placeholder="Search members"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <ul className="mt-4 space-y-3">
          {filtered.map((m) => (
            <li
              key={m.username}
              className="flex items-center justify-between rounded-lg border bg-white p-4"
            >
              <div>
                <p className="font-medium">{m.username}</p>
                <p className="text-sm text-slate-600">{m.full_name}</p>
                <p className="text-xs text-slate-400">{m.department || "—"}</p>
                <p className="text-xs">
                  {m.has_face_template ? "Face template OK" : "Missing template"}
                </p>
              </div>
              <Button variant="danger" onClick={() => setPendingDelete(m.username)}>
                Delete
              </Button>
            </li>
          ))}
        </ul>
      </div>
      {pendingDelete && (
        <Card className="mt-4 border-red-200">
          <p>Delete <strong>{pendingDelete}</strong>? This removes embeddings and images.</p>
          <div className="mt-3 flex gap-2">
            <Button variant="danger" onClick={() => deleteMember(pendingDelete)}>
              Confirm delete
            </Button>
            <Button variant="secondary" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
          </div>
        </Card>
      )}
    </ProtectedRoute>
  );
}
