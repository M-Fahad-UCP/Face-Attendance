# Face Attendance System

An AI-assisted attendance prototype built for **Windows development** and **Render free-tier** hosting. It detects faces with **InsightFace** (SCRFD + ArcFace-style embeddings), matches identities using **cosine similarity** in **NumPy**, and stores attendance rows in a lightweight **CSV** file. A **SQLite** database backs **bcrypt-hashed** credentials with **admin** vs **client** roles.

## Features

- InsightFace `FaceAnalysis` with **CPU-only ONNX Runtime** (`CPUExecutionProvider`).
- Default model preference **`buffalo_sc`** (override with `INSIGHTFACE_MODEL=buffalo_s` locally if desired).
- Automatic model download to `~/.insightface` on first inference.
- Single global model instance (lazy-loaded, thread-safe).
- Embeddings stored as small `.npy` files under `database/embeddings/`.
- Optional compressed JPEG references under `database/images/<username>/`.
- Streamlit UI with login, signup (mandatory face images), dashboards, and attendance marking.
- **Render** mode: image upload / browser capture only (no server-side webcam).
- **Local** mode: adds OpenCV **webcam burst** path (still uses `opencv-python-headless`).

## Machine learning concepts

- **Face detection** — locate faces and confidence scores.
- **Face alignment & embedding** — map each face to a fixed-length identity vector.
- **Metric learning / similarity search** — cosine similarity against a tiny gallery (matrix–vector dot product when vectors are L2-normalised).
- **Template averaging** — multiple registration crops averaged into one prototype embedding.

## Default administrator

On first startup the SQLite schema is created and **exactly one** admin row is inserted (unless one already exists):

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |
| Role     | `admin`    |

Change this password immediately from the **Admin dashboard**.

## Project layout

```text
Face-Attendance-System/
├── app.py
├── requirements.txt
├── runtime.txt
├── render.yaml
├── README.md
├── attendance/
│   └── attendance.csv
├── database/
│   ├── embeddings/
│   ├── images/
│   └── users.db          # created at runtime
├── src/
│   ├── auth.py
│   ├── dashboard.py
│   ├── face_detector.py
│   ├── face_recognizer.py
│   ├── attendance_manager.py
│   ├── register_user.py
│   ├── camera.py
│   ├── utils.py
│   ├── config.py
│   └── logger.py
├── assets/
├── screenshots/
└── logs/                 # created at runtime (app.log)
```

## Windows setup (Python 3.10)

Open **PowerShell** in the project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

python -m pip install onnxruntime
python -m pip install insightface==0.7.3
python -m pip install opencv-python-headless
python -m pip install numpy pandas pillow streamlit bcrypt
```

Or install everything from the lock file:

```powershell
python -m pip install -r requirements.txt
```

### Optional: full OpenCV wheel (local GUI / extra codecs)

The repo targets **`opencv-python-headless`** so Linux/Render installs stay small. If you need classic OpenCV extras on Windows, you can install `opencv-python` **instead** in a dedicated virtual environment (not required for this app).

### Fallback if `insightface` fails to install from PyPI

```powershell
python -m pip install git+https://github.com/deepinsight/insightface.git
```

### Run locally

```powershell
streamlit run app.py
```

The app listens on `http://localhost:8501` by default.

## Render deployment

1. Push this repository to GitHub/GitLab.
2. Create a **Web Service** and point it to the repo, **or** use the included `render.yaml` blueprint.
3. Ensure **Python 3.10** (`runtime.txt` already pins `python-3.10.13`).
4. **Start command** (already in `render.yaml`):

   ```bash
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

5. Set environment variable `INSIGHTFACE_MODEL=buffalo_sc` for the smallest download and lowest RAM footprint (already suggested in `render.yaml`).

> **Ephemeral disk:** On Render free tier, SQLite, CSV, and embeddings may reset when the instance restarts unless you attach a persistent disk or external storage.

## Authentication & roles

- Passwords are stored with **bcrypt** (salted hashes only).
- **Session timeout** defaults to 30 minutes (`SESSION_TIMEOUT_SECONDS` env override).
- **Brute-force soft lock** after repeated failed logins (`MAX_LOGIN_ATTEMPTS`, `LOGIN_LOCKOUT_SECONDS`).

### Admin capabilities

- View global metrics and attendance table.
- Register client users with face templates.
- Delete client accounts (DB row + embedding + JPEG folder).
- Export CSV, reset attendance log, inspect log tail, change admin password.

### Client capabilities

- Sign up (with mandatory face images) — always the `user` role.
- Mark attendance for **their own** identity match only.
- View personal attendance history and profile.

## Performance & memory notes

- Model pack **`buffalo_sc`** is the smallest official bundle — prefer it on **512 MB–1 GB** RAM hosts.
- Frames are resized before detection; the webcam burst path skips frames (`FRAME_SKIP` in `src/config.py`).
- Embeddings are loaded into memory **once** and refreshed only when files change.
- InsightFace is **not** imported until a face endpoint runs, keeping Streamlit cold starts lean.

## Troubleshooting

| Symptom | Mitigation |
|---------|------------|
| First run slow / timeout on Render | Model download + extraction; redeploy once `~/.insightface` is warm or use a persistent disk. |
| `insightface` import error | Reinstall with the git URL above; verify Python 3.10. |
| Webcam not opening locally | Privacy settings / device index; try **Upload / snap** mode instead. |
| Always `Unknown` | Lower the recognition threshold slightly from the admin slider; retake brighter registration photos. |
| SQLite locked | Render free tier is single-instance — avoid concurrent writes from multiple replicas without a disk. |

## Licence

InsightFace and its weights follow the upstream licences — review [deepinsight/insightface](https://github.com/deepinsight/insightface) before production redistribution.
