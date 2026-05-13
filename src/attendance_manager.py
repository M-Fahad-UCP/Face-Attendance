"""
CSV-backed attendance log.

Schema: username,full_name,date,time
- One row per (username, date)
- Auto-creates the CSV with header if missing
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import ATTENDANCE_CSV, ATTENDANCE_DIR
from src.logger import get_logger
from src.utils import now_iso, today_iso

log = get_logger("attendance")

_HEADER = ["username", "full_name", "date", "time"]


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def _ensure_csv() -> None:
    ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)
    if not ATTENDANCE_CSV.exists():
        with ATTENDANCE_CSV.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(_HEADER)
        log.info("Created attendance CSV at %s", ATTENDANCE_CSV)


def _read_df() -> pd.DataFrame:
    _ensure_csv()
    try:
        df = pd.read_csv(ATTENDANCE_CSV, dtype=str).fillna("")
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=_HEADER)
    # Guard against legacy/empty files missing columns.
    for col in _HEADER:
        if col not in df.columns:
            df[col] = ""
    return df[_HEADER]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def already_marked_today(username: str) -> bool:
    df = _read_df()
    if df.empty:
        return False
    today = today_iso()
    return bool(((df["username"] == username) & (df["date"] == today)).any())


def mark_attendance(username: str, full_name: str) -> bool:
    """
    Append an attendance row for *today*. Returns False if the user has
    already been marked today (no duplicate rows per day).
    """
    if not username:
        return False
    if already_marked_today(username):
        return False

    _ensure_csv()
    with ATTENDANCE_CSV.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([username, full_name, today_iso(), now_iso()])

    log.info("Attendance marked: %s (%s)", username, full_name)
    return True


def get_attendance(username: Optional[str] = None) -> pd.DataFrame:
    """Return the full log, or only rows for *username* if provided."""
    df = _read_df()
    if username is not None:
        df = df[df["username"] == username]
    return df.reset_index(drop=True)


def todays_count() -> int:
    df = _read_df()
    if df.empty:
        return 0
    return int((df["date"] == today_iso()).sum())


def reset_attendance() -> Path:
    """Truncate the CSV (keeps header). Returns the file path."""
    ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)
    with ATTENDANCE_CSV.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(_HEADER)
    log.info("Attendance CSV reset.")
    return ATTENDANCE_CSV


def attendance_csv_bytes() -> bytes:
    """Return the raw UTF-8 CSV bytes for download buttons."""
    _ensure_csv()
    return ATTENDANCE_CSV.read_bytes()
