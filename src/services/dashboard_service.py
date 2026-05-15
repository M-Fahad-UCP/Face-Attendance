"""Dashboard aggregates for admin and member views."""

from __future__ import annotations

from typing import Any, List

import pandas as pd

from src.attendance_manager import get_attendance, get_today_record, has_checked_out_today
from src.auth import ROLE_USER, User, list_users
from src.activity_log import recent_events
from src.analytics import summarize_presence
from src.services.reports_service import events_to_rows
from src.utils import today_iso


def today_attendance_roster() -> list[dict[str, Any]]:
    df = get_attendance()
    if df is None or df.empty:
        return []
    today = today_iso()
    today_df = df[df["date"].astype(str) == today]
    if today_df.empty:
        return []
    rows: list[dict[str, Any]] = []
    for _, row in today_df.iterrows():
        check_out = str(row.get("check_out_time", "") or "").strip()
        rows.append(
            {
                "username": str(row["username"]),
                "full_name": str(row["full_name"]),
                "check_in_time": str(row.get("time", "") or ""),
                "check_out_time": check_out,
                "checked_out": bool(check_out),
            }
        )
    rows.sort(key=lambda r: str(r["full_name"]).lower())
    return rows


def admin_dashboard(*, match_scores: List[float] | None = None) -> dict[str, Any]:
    users = list_users()
    clients = [u for u in users if u.role == ROLE_USER]
    total_users = len(clients)
    df = get_attendance()
    today = today_iso()
    present, absent, _ = summarize_presence(df, today=today, total_users=total_users)
    scores = match_scores or []
    avg_conf = float(sum(scores) / len(scores)) if scores else None

    return {
        "total_members": total_users,
        "present_today": present,
        "absent_estimate": absent,
        "avg_match_confidence": avg_conf,
        "recent_activity": events_to_rows(recent_events(25)),
        "today_attendance": today_attendance_roster(),
    }


def user_dashboard(user: User) -> dict[str, Any]:
    rec = get_today_record(user.username)
    checked_in = rec is not None
    checked_out = has_checked_out_today(user.username) if checked_in else False
    return {
        "username": user.username,
        "full_name": user.full_name,
        "checked_in_today": checked_in,
        "checked_out_today": checked_out,
        "check_in_time": rec.get("time", "") if rec else "",
        "check_out_time": rec.get("check_out_time", "") if rec else "",
    }


def weekly_check_ins(df: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    if df is None:
        df = get_attendance()
    if df is None or df.empty or "date" not in df.columns:
        return []
    counts = (
        df.assign(date=df["date"].astype(str))
        .groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "check_ins"})
        .sort_values("date")
        .tail(14)
    )
    return [
        {"date": str(row["date"]), "check_ins": int(row["check_ins"])}
        for _, row in counts.iterrows()
    ]


def top_members_by_checkins(df: pd.DataFrame, limit: int = 12) -> list[dict[str, Any]]:
    if df is None or df.empty or "username" not in df.columns:
        return []
    top = (
        df.groupby("username", as_index=False)
        .size()
        .rename(columns={"size": "check_ins"})
        .sort_values("check_ins", ascending=False)
        .head(limit)
    )
    return [
        {"username": str(row["username"]), "check_ins": int(row["check_ins"])}
        for _, row in top.iterrows()
    ]
