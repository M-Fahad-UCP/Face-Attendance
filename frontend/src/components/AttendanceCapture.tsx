"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { RecognizeResult } from "@/lib/types";
import { Button, Card } from "./ui";

type Props = {
  onMarked?: () => void;
};

export function AttendanceCapture({ onMarked }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastFileRef = useRef<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<RecognizeResult | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraOn(false);
  }, []);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Attach stream after <video> is in the DOM (fixes blank preview).
  useEffect(() => {
    if (!cameraOn || !streamRef.current) return;
    const video = videoRef.current;
    if (!video) return;
    video.srcObject = streamRef.current;
    video.play().catch(() => {
      setMessage("Could not start video playback — try Upload instead.");
    });
  }, [cameraOn]);

  async function runRecognition(file: File) {
    setLoading(true);
    setMessage("");
    lastFileRef.current = file;
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

  function notifyMarked(res: { ok: boolean; message: string; already_today?: boolean }) {
    setMessage(res.message);
    if (res.ok || res.already_today) {
      onMarked?.();
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
        already_today?: boolean;
      }>("/api/attendance/mark", {
        method: "POST",
        json: { username: result.primary_username },
      });
      notifyMarked(res);
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
      const res = await api<{ ok: boolean; message: string; already_today?: boolean }>(
        "/api/attendance/mark-from-image",
        { method: "POST", formData: fd }
      );
      notifyMarked(res);
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
    setMessage("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      setCameraOn(true);
    } catch {
      setMessage("Camera access denied or unavailable.");
    }
  }

  async function waitForVideoReady(video: HTMLVideoElement): Promise<void> {
    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA && video.videoWidth > 0) {
      return;
    }
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("Camera not ready")), 8000);
      video.onloadedmetadata = () => {
        clearTimeout(timeout);
        resolve();
      };
    });
  }

  async function captureFromCamera() {
    const video = videoRef.current;
    if (!video) {
      setMessage("Camera not ready — wait a moment and try again.");
      return;
    }
    try {
      await waitForVideoReady(video);
    } catch {
      setMessage("Camera feed not ready yet — wait a second and capture again.");
      return;
    }
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      setMessage("No video frame available — close and reopen the camera.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.92)
    );
    if (!blob) {
      setMessage("Failed to capture frame.");
      return;
    }
    const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
    setPreview(URL.createObjectURL(blob));
    await runRecognition(file);
  }

  const successMsg =
    message.includes("saved") ||
    message.includes("Saved") ||
    message.includes("Already checked") ||
    message.includes("checked in");

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
          <video
            ref={videoRef}
            className="mt-4 w-full max-w-lg rounded-lg border bg-black object-cover"
            style={{ minHeight: 240, maxHeight: 360 }}
            autoPlay
            playsInline
            muted
          />
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
          <div className="mt-4 flex flex-wrap gap-3">
            <Button onClick={confirmMark} disabled={loading}>
              Confirm attendance
            </Button>
            <Button
              variant="secondary"
              disabled={loading}
              onClick={() => {
                const f = lastFileRef.current ?? fileRef.current?.files?.[0];
                if (f) markFromImage(f);
                else setMessage("Capture or upload an image first.");
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
            successMsg ? "bg-green-50 text-green-800" : "bg-amber-50 text-amber-800"
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
