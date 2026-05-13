"""Append-only JSONL feed for the admin \"Recent activity\" panel."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

from src.config import LOGS_DIR

_PATH = LOGS_DIR / "activity.jsonl"
_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_event(kind: str, message: str, **extra: Any) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now_iso(), "kind": kind, "message": message, **extra}
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with _LOCK:
        with _PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)


def recent_events(limit: int = 40) -> List[dict[str, Any]]:
    if not _PATH.exists():
        return []
    try:
        lines = _PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out: List[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))
