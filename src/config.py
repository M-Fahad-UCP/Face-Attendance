"""
Central configuration for the Face Attendance System.

All paths use pathlib so the project works on both Windows (local dev)
and Linux (Render free tier). Constants here are tuned for low RAM and
CPU-only execution.
"""

from __future__ import annotations

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent

DATABASE_DIR: Path = BASE_DIR / "database"
EMBEDDINGS_DIR: Path = DATABASE_DIR / "embeddings"
IMAGES_DIR: Path = DATABASE_DIR / "images"
USERS_DB_PATH: Path = DATABASE_DIR / "users.db"

ATTENDANCE_DIR: Path = BASE_DIR / "attendance"
ATTENDANCE_CSV: Path = ATTENDANCE_DIR / "attendance.csv"

ASSETS_DIR: Path = BASE_DIR / "assets"
LOGS_DIR: Path = BASE_DIR / "logs"


def ensure_directories() -> None:
    """Create all required folders on first run. Safe to call repeatedly."""
    for path in (
        DATABASE_DIR,
        EMBEDDINGS_DIR,
        IMAGES_DIR,
        ATTENDANCE_DIR,
        ASSETS_DIR,
        LOGS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Default admin credentials (created only if no admin row exists)
# ---------------------------------------------------------------------------
DEFAULT_ADMIN_USERNAME: str = "admin"
DEFAULT_ADMIN_PASSWORD: str = "admin123"
DEFAULT_ADMIN_FULLNAME: str = "System Administrator"

ROLE_ADMIN: str = "admin"
ROLE_USER: str = "user"


# ---------------------------------------------------------------------------
# InsightFace / ONNX configuration (low-memory friendly)
# ---------------------------------------------------------------------------
# buffalo_sc is the smallest official model pack (~16 MB) and is the only
# one safe to load on Render's free 512 MB tier alongside Streamlit.
INSIGHTFACE_MODEL_NAME: str = os.environ.get("INSIGHTFACE_MODEL", "buffalo_sc")
INSIGHTFACE_PROVIDERS: list[str] = ["CPUExecutionProvider"]

# Smaller det_size = lower RAM, faster CPU inference.
INSIGHTFACE_DET_SIZE: tuple[int, int] = (320, 320)
INSIGHTFACE_CTX_ID: int = 0  # 0 => CPU when only CPUExecutionProvider is given.


# ---------------------------------------------------------------------------
# Recognition tuning
# ---------------------------------------------------------------------------
# Cosine similarity threshold for "same person". Embeddings from
# InsightFace are L2-normalised, so cosine sim ranges in [-1, 1].
RECOGNITION_THRESHOLD: float = 0.45

# Frame-skip for the live webcam loop (process every Nth frame).
FRAME_SKIP: int = 3

# Resize webcam frames to this width before detection (keeps aspect ratio).
PROCESSING_FRAME_WIDTH: int = 480

# Number of face captures requested during registration.
REGISTRATION_CAPTURES: int = 5

# Webcam burst: discard early frames (autofocus / black frames), then sample densely.
BURST_DURATION_SEC: float = float(os.environ.get("BURST_DURATION_SEC", "3.5"))
BURST_WARMUP_READS: int = int(os.environ.get("BURST_WARMUP_READS", "28"))
BURST_FRAME_SKIP: int = int(os.environ.get("BURST_FRAME_SKIP", "1"))
BURST_MAX_WIDTH: int = int(os.environ.get("BURST_MAX_WIDTH", "640"))
def is_render_env() -> bool:
    """True when running on a Render web service (no local webcam access)."""
    return any(k in os.environ for k in ("RENDER", "RENDER_SERVICE_ID"))


# ---------------------------------------------------------------------------
# Session / security
# ---------------------------------------------------------------------------
SESSION_TIMEOUT_SECONDS: int = int(os.environ.get("SESSION_TIMEOUT_SECONDS", "1800"))
MAX_LOGIN_ATTEMPTS: int = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_LOCKOUT_SECONDS: int = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "120"))

# Browser session cookie (signed). Set SESSION_SIGNING_SECRET on production hosts.
SESSION_COOKIE_NAME: str = os.environ.get("SESSION_COOKIE_NAME", "fa_session")
SESSION_SIGNING_SECRET: str = os.environ.get("SESSION_SIGNING_SECRET", "").strip()
