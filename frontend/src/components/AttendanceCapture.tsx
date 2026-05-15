"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api";
import type { RecognizeResult } from "@/lib/types";
import { Button, Card } from "./ui";

export function AttendanceCapture() {
  const fileRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<RecognizeResult | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);

  async function runRecognition(file: File) {
    setLoading(true);
    setMessage("");
    const fd = new FormData();
    fd.append("image", file);
    try {
      const res = await api<RecognizeResult>("/api/recognize", {
        method: "POST",
        formData: fd,
      });
      setResult(res);
      if (res.preview_base64) {
        setPreview(`data:image/jpeg;base64,${res.preview_base64}`);
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Recognition failed");
    } finally {
      setLoading(false);
    }
  }

  async function confirmMark() {
    if (!result?.primary_username || result.primary_username === "Unknown") {
      setMessage("No matched identity to mark.");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      const res = await api<{
        ok: boolean;
        message: string;
      }>("/api/attendance/mark", {
        method: "POST",
        json: { username: result.primary_username },
      });
      setMessage(res.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Mark failed");
    } finally {
      setLoading(false);
    }
  }

  async function markFromImage(file: File) {
    setLoading(true);
    setMessage("");
    const fd = new FormData();
    fd.append("image", file);
    try {
      const res = await api<{ ok: boolean; message: string }>(
        "/api/attendance/mark-from-image",
        { method: "POST", formData: fd }
      );
      setMessage(res.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Mark failed");
    } finally {
      setLoading(false);
    }
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    runRecognition(file);
  }

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);
    } catch {
      setMessage("Camera access denied or unavailable.");
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOn(false);
  }

  async function captureFromCamera() {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
      setPreview(URL.createObjectURL(blob));
      await runRecognition(file);
    }, "image/jpeg");
  }

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-lg font-semibold text-slate-900">Mark attendance</h2>
        <p className="mt-1 text-sm text-slate-500">
          Upload a selfie or use your browser camera. Recognition runs on the server.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg"
            className="hidden"
            onChange={onFileChange}
          />
          <Button type="button" onClick={() => fileRef.current?.click()} disabled={loading}>
            Upload image
          </Button>
          {!cameraOn ? (
            <Button type="button" variant="secondary" onClick={startCamera}>
              Open camera
            </Button>
          ) : (
            <>
              <Button type="button" onClick={captureFromCamera} disabled={loading}>
                Capture frame
              </Button>
              <Button type="button" variant="secondary" onClick={stopCamera}>
                Close camera
              </Button>
            </>
          )}
        </div>
        {cameraOn && (
          <video ref={videoRef} className="mt-4 max-h-64 rounded-lg border" playsInline muted />
        )}
      </Card>

      {preview && (
        <Card>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview} alt="Preview" className="max-h-80 rounded-lg" />
        </Card>
      )}

      {result && (
        <Card>
          <p className="text-sm text-slate-600">
            Threshold: {result.threshold.toFixed(2)} · Primary:{" "}
            <strong>{result.primary_username}</strong>
          </p>
          <ul className="mt-3 space-y-2">
            {result.faces.map((f, i) => (
              <li key={i} className="text-sm">
                {f.username} — score {(f.score * 100).toFixed(1)}%
                {f.matched ? " ✓" : ""}
              </li>
            ))}
          </ul>
          <div className="mt-4 flex gap-3">
            <Button onClick={confirmMark} disabled={loading}>
              Confirm attendance
            </Button>
            <Button
              variant="secondary"
              disabled={loading}
              onClick={() => {
                const f = fileRef.current?.files?.[0];
                if (f) markFromImage(f);
              }}
            >
              Mark in one step
            </Button>
          </div>
        </Card>
      )}

      {message && (
        <p
          className={`rounded-lg p-3 text-sm ${
            message.includes("saved") || message.includes("Saved")
              ? "bg-green-50 text-green-800"
              : "bg-amber-50 text-amber-800"
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
