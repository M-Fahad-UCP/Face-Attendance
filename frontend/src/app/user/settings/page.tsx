"use client";

import { useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Button, Card, Label } from "@/components/ui";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

export default function UserSettingsPage() {
  const { user } = useAuth();
  const [files, setFiles] = useState<File[]>([]);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function updateFace() {
    if (!files.length) {
      setMsg("Select 1–5 face photos first.");
      return;
    }
    setLoading(true);
    setMsg("");
    const fd = new FormData();
    files.slice(0, 5).forEach((f) => fd.append("images", f));
    try {
      await api("/api/users/me/face", { method: "POST", formData: fd });
      setMsg("Face photos updated. Try attendance again with good lighting.");
      setFiles([]);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Update failed");
    } finally {
      setLoading(false);
    }
  }

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
      <Card className="mt-6">
        <h2 className="font-semibold">Update face photos</h2>
        <p className="mt-1 text-sm text-slate-500">
          Re-enroll if recognition fails or your appearance changed. Upload 1–5 clear front-facing photos.
        </p>
        <div className="mt-4">
          <Label>New face photos</Label>
          <input
            type="file"
            accept="image/png,image/jpeg"
            multiple
            className="mt-2 block w-full text-sm"
            onChange={(e) => setFiles(Array.from(e.target.files || []))}
          />
        </div>
        <Button className="mt-4" onClick={updateFace} disabled={loading}>
          {loading ? "Uploading…" : "Save new face template"}
        </Button>
        {msg && <p className="mt-3 text-sm text-slate-600">{msg}</p>}
      </Card>
    </ProtectedRoute>
  );
}
