"""
Lightweight logging helper. One rotating-style log file under logs/.
Falls back to stream logging if the file cannot be opened (e.g. read-only FS).
"""

from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from src.config import LOGS_DIR, ensure_directories

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialised = False


def _init_root() -> None:
    global _initialised
    if _initialised:
        return

    ensure_directories()
    root = logging.getLogger("face_attendance")
    root.setLevel(logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    try:
        log_path: Path = LOGS_DIR / "app.log"
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # Read-only filesystem on some hosts; keep stream logging only.
        pass

    _initialised = True


def get_logger(name: str) -> Logger:
    """Return a namespaced logger sharing the project's handlers."""
    _init_root()
    return logging.getLogger(f"face_attendance.{name}")
