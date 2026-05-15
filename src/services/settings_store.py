"""Persist admin-tunable settings (recognition threshold) outside Streamlit session."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from src.config import DATABASE_DIR, RECOGNITION_THRESHOLD

_SETTINGS_PATH = DATABASE_DIR / "settings.json"
_LOCK = threading.Lock()


def _read() -> dict[str, Any]:
    if not _SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write(data: dict[str, Any]) -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_recognition_threshold() -> float:
    with _LOCK:
        raw = _read().get("recognition_threshold")
    if raw is None:
        return float(RECOGNITION_THRESHOLD)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(RECOGNITION_THRESHOLD)


def set_recognition_threshold(value: float) -> float:
    clamped = max(0.2, min(0.8, float(value)))
    with _LOCK:
        data = _read()
        data["recognition_threshold"] = clamped
        _write(data)
    return clamped
