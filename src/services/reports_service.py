"""Reports filtering and export (no Streamlit dependency)."""

from __future__ import annotations

import io
from typing import Any, Optional

import pandas as pd

from src.attendance_manager import attendance_csv_bytes, get_attendance
from src.auth import User
from src.utils import today_iso


def enrich_attendance_with_members(df: pd.DataFrame, users: list[User]) -> pd.DataFrame:
    if df is None or df.empty:
        out = df.copy() if df is not None else pd.DataFrame()
        if out.empty and len(out.columns) == 0:
            return pd.DataFrame(
                columns=[
                    "username",
                    "full_name",
                    "date",
                    "time",
                    "department",
                    "member_role",
                    "record_status",
                ]
            )
        out["department"] = ""
        out["member_role"] = ""
        out["record_status"] = ""
        return out
    out = df.copy()
    dept: dict[str, str] = {}
    role_map: dict[str, str] = {}
    for u in users:
        dept[u.username] = u.department or ""
        role_map[u.username] = u.role
    out["department"] = out["username"].astype(str).map(lambda x: dept.get(x, ""))
    out["member_role"] = out["username"].astype(str).map(lambda x: role_map.get(x, ""))
    out["record_status"] = "Check-in"
    return out


def filter_dataframe(
    df: pd.DataFrame,
    *,
    q: str,
    username: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> pd.DataFrame:
    out = df.copy()
    if username and "username" in out.columns:
        out = out[out["username"].astype(str) == username]
    if date_from and "date" in out.columns:
        out = out[out["date"].astype(str) >= date_from]
    if date_to and "date" in out.columns:
        out = out[out["date"].astype(str) <= date_to]
    q = (q or "").strip().lower()
    if q and not out.empty:
        tokens = [t for t in q.split() if t]

        def row_matches(row: pd.Series) -> bool:
            blob = " ".join(str(v).lower() for v in row.values)
            return all(t in blob for t in tokens)

        out = out[out.apply(row_matches, axis=1)]
    return out.reset_index(drop=True)


def filter_reports(
    df: pd.DataFrame,
    *,
    q: str = "",
    username: Optional[str] = None,
    department: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    today_only: bool = False,
) -> pd.DataFrame:
    out = filter_dataframe(
        df, q=q, username=username, date_from=date_from, date_to=date_to
    )
    if department and "department" in out.columns and department != "(All)":
        out = out[out["department"].astype(str) == department]
    if today_only and "date" in out.columns:
        out = out[out["date"].astype(str) == today_iso()]
    return out.reset_index(drop=True)


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    return df.fillna("").astype(str).to_dict(orient="records")


def filtered_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def events_to_rows(events: list) -> list[dict[str, str]]:
    rows = []
    for ev in events:
        rows.append(
            {
                "time_utc": str(ev.get("ts") or ""),
                "category": str(ev.get("kind") or ""),
                "summary": str(ev.get("message") or ""),
                "related_member": str(ev.get("username") or "—"),
            }
        )
    return rows
