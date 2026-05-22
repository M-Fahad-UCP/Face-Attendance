# Face Attendance System

AI-assisted attendance with **InsightFace** (SCRFD + embeddings), **Python FastAPI** backend, and **Next.js 14** frontend (TypeScript, Tailwind).

## Architecture

| Layer | Stack |
|-------|--------|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind, zod, Recharts |
| API | FastAPI, Pydantic, session cookies + Bearer JWT |
| ML | Python 3.10, InsightFace, ONNX Runtime (CPU), OpenCV |
| Data | SQLite (users), CSV (attendance), `.npy` embeddings |

```text
frontend/     → UI (port 3000)
api/          → HTTP API (port 8000)
src/          → Auth, recognition, services
database/     → users.db, embeddings/, images/
attendance/   → attendance.csv
```

## Quick start (local)

### 1. Python API

```powershell
cd "Face Attendance"
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_api.py
```

> Use **Python 3.10** (see `runtime.txt`). The default `python` on Windows may be 3.13, which can fail to build pinned packages like `pandas==2.2.1`.

API: http://localhost:8000 — docs at http://localhost:8000/api/docs

### 2. Next.js frontend

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

Default admin (created on first API start): `admin` / `admin123`

## Environment variables

| Variable | Where | Purpose |
|----------|--------|---------|
| `DATA_ROOT` | API | Persistent data root (use `/data` on Render with attached disk) |
| `SESSION_SIGNING_SECRET` | API | Signed session tokens (set in production) |
| `CORS_ORIGINS` | API | Comma-separated frontend URLs |
| `INSIGHTFACE_MODEL` | API | Default `buffalo_sc` |
| `NEXT_PUBLIC_API_URL` | Frontend | e.g. `http://localhost:8000` |

## New capabilities

- **SQLite attendance** (migrates legacy CSV on first run) with check-in and check-out
- **Member check-out** from the Attendance page
- **Face re-enrollment** under member Settings (`POST /api/users/me/face`)
- **Admin**: edit member profile, manual present today, audit log page
- **Render disk** via `DATA_ROOT=/data` in [`render.yaml`](render.yaml)

## Deployment

### API (Render)

`render.yaml` runs:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Set `CORS_ORIGINS` to your frontend URL and `SESSION_SIGNING_SECRET`.

### Frontend (Render)

Deploy `frontend/` as a Render **Web Service**:

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Build Command | `npm install && npm run build` |
| Start Command | `npm start` |
| Environment | `NEXT_PUBLIC_API_URL` → the Render API URL above |

Use Node 20+ (set `NODE_VERSION=20` in Environment if Render's default differs).

## Features

- Admin: dashboard, attendance, member registration with face templates, reports, analytics, settings
- Members: self-signup with face photos, mark own attendance, personal reports
- Recognition via uploaded image or browser camera (frames sent to API)
- bcrypt passwords, role-based access, login lockout

## Default administrator

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

Change the password from **Admin → Settings** after first login.

## Licence

InsightFace weights follow upstream licences — see [deepinsight/insightface](https://github.com/deepinsight/insightface).
