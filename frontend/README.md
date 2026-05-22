# Face Attendance — Frontend

Next.js 14 (App Router) + TypeScript + Tailwind + Framer Motion. Talks to the FastAPI backend in `../api/`.

## Local development

```bash
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

App: http://localhost:3000

## Environment

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend (e.g. `http://localhost:8000` locally, your Render API URL in production) |

## Build

```bash
npm run build && npm start
```

## Deployment (Render)

Configure as a Render **Web Service**:

- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Start Command: `npm start`
- Environment: `NEXT_PUBLIC_API_URL` pointing at the API service
- Node version: 20+ (set `NODE_VERSION=20` if Render's default differs)

See the repo root [README.md](../README.md) for the full architecture overview.
