"""
SQLite-backed attendance storage with one row per (username, date).

Migrates legacy CSV data on first init.
"""

from __future__ import annotations

import csv
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

import pandas as pd

from src.config import ATTENDANCE_CSV, ATTENDANCE_DB_PATH, WORK_START_TIME, ensure_directories
from src.logger import get_logger
from src.utils import now_iso, today_iso

log = get_logger("attendance_store")

_COLUMNS = [
    "username",
    "full_name",
    "date",
    "time",
    "check_out_time",
    "status",
    "source",
]


def _is_late(check_in_time: str) -> str:
    try:
        start = datetime.strptime(WORK_START_TIME.strip(), "%H:%M").time()
        actual = datetime.strptime(check_in_time.strip(), "%H:%M:%S").time()
        return "late" if actual > start else "on_time"
    except ValueError:
        return "on_time"


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    ensure_directories()
    conn = sqlite3.connect(str(ATTENDANCE_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_attendance_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_records (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT NOT NULL,
                full_name       TEXT NOT NULL,
                date            TEXT NOT NULL,
                check_in_time   TEXT NOT NULL,
                check_out_time  TEXT NOT NULL DEFAULT '',
                status          TEXT NOT NULL DEFAULT 'on_time',
                source          TEXT NOT NULL DEFAULT 'face',
                UNIQUE(username, date)
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_records(date);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_user_date "
            "ON attendance_records(username, date);"
        )
    _migrate_csv_if_needed()


def _migrate_csv_if_needed() -> None:
    if not ATTENDANCE_CSV.exists():
        return
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM attendance_records").fetchone()
        if count and int(count["c"]) > 0:
            return
        try:
            with ATTENDANCE_CSV.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
        except OSError:
            return
        if not rows:
            return
        for row in rows:
            username = (row.get("username") or "").strip()
            if not username:
                continue
            full_name = (row.get("full_name") or "").strip()
            date = (row.get("date") or "").strip()
            check_in = (row.get("time") or now_iso()).strip()
            status = _is_late(check_in)
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO attendance_records
                    (username, full_name, date, check_in_time, check_out_time, status, source)
                    VALUES (?, ?, ?, ?, '', ?, 'migrated')
                    """,
                    (username, full_name, date, check_in, status),
                )
            except sqlite3.Error:
                continue
        log.info("Migrated %d attendance rows from CSV to SQLite.", len(rows))


def _row_to_dict(row: sqlite3.Row) -> dict[str, str]:
    return {
        "username": str(row["username"]),
        "full_name": str(row["full_name"]),
        "date": str(row["date"]),
        "time": str(row["check_in_time"]),
        "check_out_time": str(row["check_out_time"] or ""),
        "status": str(row["status"] or "on_time"),
        "source": str(row["source"] or "face"),
    }


def get_today_record(username: str) -> Optional[dict[str, str]]:
    init_attendance_db()
    uname = username.strip().lower()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM attendance_records
            WHERE lower(username) = ? AND date = ?
            """,
            (uname, today_iso()),
        ).fetchone()
    return _row_to_dict(row) if row else None


def already_marked_today(username: str) -> bool:
    return get_today_record(username) is not None


def has_checked_out_today(username: str) -> bool:
    rec = get_today_record(username)
    if not rec:
        return False
    return bool(rec.get("check_out_time", "").strip())


def mark_check_in(username: str, full_name: str, *, source: str = "face") -> bool:
    if not username:
        return False
    if already_marked_today(username):
        return False
    init_attendance_db()
    check_in = now_iso()
    status = _is_late(check_in)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO attendance_records
            (username, full_name, date, check_in_time, check_out_time, status, source)
            VALUES (?, ?, ?, ?, '', ?, ?)
            """,
            (username, full_name, today_iso(), check_in, status, source),
        )
    log.info("Check-in: %s (%s) status=%s", username, full_name, status)
    return True


def mark_check_out(username: str) -> bool:
    rec = get_today_record(username)
    if rec is None:
        return False
    if rec.get("check_out_time", "").strip():
        return False
    with _connect() as conn:
        cur = conn.execute(
            """
            UPDATE attendance_records
            SET check_out_time = ?
            WHERE lower(username) = ? AND date = ?
            """,
            (now_iso(), username.strip().lower(), today_iso()),
        )
        return cur.rowcount > 0


def mark_manual_present(
    username: str,
    full_name: str,
    *,
    reason: str = "",
) -> bool:
    """Admin override: ensure a check-in row exists for today."""
    if already_marked_today(username):
        return False
    ok = mark_check_in(username, full_name, source=f"manual:{reason[:40]}")
    return ok


def fetch_dataframe(username: Optional[str] = None) -> pd.DataFrame:
    init_attendance_db()
    query = "SELECT username, full_name, date, check_in_time, check_out_time, status, source FROM attendance_records"
    params: tuple = ()
    if username is not None:
        query += " WHERE username = ?"
        params = (username,)
    query += " ORDER BY date DESC, check_in_time DESC"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    if not rows:
        return pd.DataFrame(columns=_COLUMNS)
    records = [_row_to_dict(r) for r in rows]
    df = pd.DataFrame(records)
    df["record_status"] = df.apply(
        lambda r: "Checked out"
        if str(r.get("check_out_time", "")).strip()
        else ("Late" if r.get("status") == "late" else "On time"),
        axis=1,
    )
    return df


def reset_all() -> Path:
    init_attendance_db()
    with _connect() as conn:
        conn.execute("DELETE FROM attendance_records")
    log.info("Attendance SQLite log cleared.")
    return ATTENDANCE_DB_PATH


def export_csv_bytes() -> bytes:
    df = fetch_dataframe()
    return df.to_csv(index=False).encode("utf-8")
