"""Dashboard aggregates for admin and member views."""

from __future__ import annotations

from typing import Any, List

import pandas as pd

from src.attendance_manager import get_attendance
from src.auth import ROLE_USER, User, list_users
from src.activity_log import recent_events
from src.analytics import summarize_presence
from src.services.reports_service import events_to_rows
from src.utils import today_iso


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
    }


def user_dashboard(user: User) -> dict[str, Any]:
    from src.attendance_manager import already_marked_today

    marked = already_marked_today(user.username)
    return {
        "username": user.username,
        "full_name": user.full_name,
        "checked_in_today": marked,
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
