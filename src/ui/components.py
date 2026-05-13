"""Reusable Streamlit UI helpers."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import streamlit as st


def empty_state(
    title: str,
    body: str,
    *,
    action_label: Optional[str] = None,
    action_key: Optional[str] = None,
) -> bool:
    """Render a centered empty state; optional CTA button. Returns True if CTA clicked."""
    st.markdown(
        f'<div class="fa-empty"><div style="font-weight:700;color:var(--fa-text);margin-bottom:0.35rem;">'
        f"{title}</div><div>{body}</div></div>",
        unsafe_allow_html=True,
    )
    if action_label and action_key:
        return st.button(action_label, key=action_key, type="primary")
    return False


def dataframe_grid(
    df: pd.DataFrame,
    *,
    height: int = 360,
    key: Optional[str] = None,
) -> None:
    """``st.dataframe`` tuned for admin grids."""
    if df is None or df.empty:
        empty_state("No records", "Try adjusting filters or date range.")
        return
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=height,
        key=key,
    )


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
        if tokens:
            def row_matches(row: pd.Series) -> bool:
                blob = " ".join(str(v).lower() for v in row.values)
                return all(t in blob for t in tokens)

            out = out[out.apply(row_matches, axis=1)]
    return out.reset_index(drop=True)


def enrich_attendance_with_members(df: pd.DataFrame, users: list) -> pd.DataFrame:
    """Add department and role from auth ``User`` rows."""
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
        dept[u.username] = getattr(u, "department", "") or ""
        role_map[u.username] = u.role
    out["department"] = out["username"].astype(str).map(lambda x: dept.get(x, ""))
    out["member_role"] = out["username"].astype(str).map(lambda x: role_map.get(x, ""))
    out["record_status"] = "Check-in"
    return out


def filter_reports_dataframe(
    df: pd.DataFrame,
    *,
    q: str,
    username: Optional[str],
    department: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    today_only: bool,
    today_iso: str,
) -> pd.DataFrame:
    out = filter_dataframe(
        df, q=q, username=username, date_from=date_from, date_to=date_to
    )
    if department and "department" in out.columns and department != "(All)":
        out = out[out["department"].astype(str) == department]
    if today_only and "date" in out.columns:
        out = out[out["date"].astype(str) == today_iso]
    return out.reset_index(drop=True)


def events_to_activity_dataframe(events: list) -> pd.DataFrame:
    """Turn JSONL activity events into a tidy table for ``st.dataframe``."""
    if not events:
        return pd.DataFrame(
            columns=["Time (UTC)", "Category", "Summary", "Related member"]
        )
    rows = []
    for ev in events:
        rows.append(
            {
                "Time (UTC)": str(ev.get("ts") or ""),
                "Category": str(ev.get("kind") or ""),
                "Summary": str(ev.get("message") or ""),
                "Related member": str(ev.get("username") or "—"),
            }
        )
    return pd.DataFrame(rows)


def confirm_checkbox(label: str, *, key: str) -> bool:
    return bool(st.checkbox(label, key=key))
