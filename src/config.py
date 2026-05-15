"""
Central configuration for the Face Attendance System.

All paths use pathlib so the project works on both Windows (local dev)
and Linux (Render free tier). Set DATA_ROOT=/data when using a Render disk.
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_data_root() -> Path:
    raw = os.environ.get("DATA_ROOT", "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent


DATA_ROOT: Path = _resolve_data_root()
BASE_DIR: Path = Path(__file__).resolve().parent.parent

DATABASE_DIR: Path = DATA_ROOT / "database"
EMBEDDINGS_DIR: Path = DATABASE_DIR / "embeddings"
IMAGES_DIR: Path = DATABASE_DIR / "images"
USERS_DB_PATH: Path = DATABASE_DIR / "users.db"
ATTENDANCE_DB_PATH: Path = DATABASE_DIR / "attendance.db"

ATTENDANCE_DIR: Path = DATA_ROOT / "attendance"
ATTENDANCE_CSV: Path = ATTENDANCE_DIR / "attendance.csv"

ASSETS_DIR: Path = BASE_DIR / "assets"
LOGS_DIR: Path = DATA_ROOT / "logs"


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


DEFAULT_ADMIN_USERNAME: str = "admin"
DEFAULT_ADMIN_PASSWORD: str = "admin123"
DEFAULT_ADMIN_FULLNAME: str = "System Administrator"

ROLE_ADMIN: str = "admin"
ROLE_USER: str = "user"

INSIGHTFACE_MODEL_NAME: str = os.environ.get("INSIGHTFACE_MODEL", "buffalo_sc")
INSIGHTFACE_PROVIDERS: list[str] = ["CPUExecutionProvider"]
INSIGHTFACE_DET_SIZE: tuple[int, int] = (320, 320)
INSIGHTFACE_CTX_ID: int = 0

RECOGNITION_THRESHOLD: float = 0.45
FRAME_SKIP: int = 3
PROCESSING_FRAME_WIDTH: int = 480
REGISTRATION_CAPTURES: int = 5

BURST_DURATION_SEC: float = float(os.environ.get("BURST_DURATION_SEC", "3.5"))
BURST_WARMUP_READS: int = int(os.environ.get("BURST_WARMUP_READS", "28"))
BURST_FRAME_SKIP: int = int(os.environ.get("BURST_FRAME_SKIP", "1"))
BURST_MAX_WIDTH: int = int(os.environ.get("BURST_MAX_WIDTH", "640"))

# Work-day policy: check-ins after this time (HH:MM, 24h) are marked "late".
WORK_START_TIME: str = os.environ.get("WORK_START_TIME", "09:00")


def is_render_env() -> bool:
    return any(k in os.environ for k in ("RENDER", "RENDER_SERVICE_ID"))


def is_production_env() -> bool:
    return is_render_env() or os.environ.get("ENV", "").lower() in ("production", "prod")


SESSION_TIMEOUT_SECONDS: int = int(os.environ.get("SESSION_TIMEOUT_SECONDS", "1800"))
MAX_LOGIN_ATTEMPTS: int = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_LOCKOUT_SECONDS: int = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "120"))

SESSION_COOKIE_NAME: str = os.environ.get("SESSION_COOKIE_NAME", "fa_session")
SESSION_SIGNING_SECRET: str = os.environ.get("SESSION_SIGNING_SECRET", "").strip()
