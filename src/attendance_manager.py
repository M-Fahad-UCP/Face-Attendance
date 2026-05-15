"""
Attendance log facade — SQLite storage (see attendance_store.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.attendance_store import (
    already_marked_today,
    export_csv_bytes,
    fetch_dataframe,
    get_today_record,
    has_checked_out_today,
    init_attendance_db,
    mark_check_in,
    mark_check_out,
    mark_manual_present,
    reset_all,
)

__all__ = [
    "init_attendance_db",
    "already_marked_today",
    "get_today_record",
    "has_checked_out_today",
    "mark_attendance",
    "mark_check_out",
    "mark_manual_present",
    "get_attendance",
    "todays_count",
    "reset_attendance",
    "attendance_csv_bytes",
]


def mark_attendance(username: str, full_name: str) -> bool:
    return mark_check_in(username, full_name, source="face")


def get_attendance(username: Optional[str] = None) -> pd.DataFrame:
    return fetch_dataframe(username)


def todays_count() -> int:
    df = fetch_dataframe()
    if df.empty:
        return 0
    from src.utils import today_iso

    return int((df["date"].astype(str) == today_iso()).sum())


def reset_attendance() -> Path:
    return reset_all()


def attendance_csv_bytes() -> bytes:
    return export_csv_bytes()
