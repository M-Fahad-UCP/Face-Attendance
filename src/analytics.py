"""Lightweight charts for attendance analytics (Plotly)."""

from __future__ import annotations

import pandas as pd


def weekly_attendance_chart(df: pd.DataFrame):
    """Return a Plotly figure or None if insufficient data."""
    import plotly.express as px

    if df is None or df.empty or "date" not in df.columns:
        return None
    counts = (
        df.assign(date=df["date"].astype(str))
        .groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "check_ins"})
        .sort_values("date")
        .tail(14)
    )
    if counts.empty:
        return None
    fig = px.bar(
        counts,
        x="date",
        y="check_ins",
        labels={"date": "Date", "check_ins": "Check-ins"},
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#334155"),
        title=dict(text="Daily check-ins (last 14 days)", font=dict(size=14)),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.25)"),
        xaxis=dict(showgrid=False),
    )
    fig.update_traces(marker_color="#4f46e5")
    return fig


def recognition_accuracy_placeholder(confidences: list[float]):
    """Small line chart for recognition scores (session analytics)."""
    import plotly.graph_objects as go

    if not confidences:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=confidences,
            mode="lines+markers",
            line=dict(color="#0d9488"),
            marker=dict(size=6),
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Recent match confidence (session)", font=dict(size=14)),
        yaxis=dict(range=[0, 1], title="Cosine similarity"),
        xaxis=dict(title="Attempt"),
    )
    return fig


def summarize_presence(df: pd.DataFrame, *, today: str, total_users: int) -> tuple[int, int, float]:
    """Present today count, absent estimate, accuracy placeholder."""
    if df is None or df.empty or "date" not in df.columns:
        return 0, max(total_users - 0, 0), 0.0
    today_df = df[df["date"].astype(str) == today]
    present = int(today_df["username"].nunique()) if not today_df.empty else 0
    absent = max(total_users - present, 0)
    # Placeholder "accuracy" — real metric would need labeled validation data
    accuracy = min(0.5 + 0.5 * (present / max(total_users, 1)), 0.99)
    return present, absent, float(accuracy)
