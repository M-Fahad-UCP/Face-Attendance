"""Analytics views (admin org-wide, member self-scoped)."""

from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from src.activity_log import recent_events
from src.analytics import recognition_accuracy_placeholder, weekly_attendance_chart
from src.attendance_manager import get_attendance
from src.auth import ROLE_ADMIN
from src.streamlit_session import state_user
from src.ui.components import empty_state, events_to_activity_dataframe


def render_analytics() -> None:
    user = state_user()
    if user is None:
        st.error("Unauthorized.")
        return

    st.markdown("### Analytics")
    st.caption("Trends and recognition quality — data refreshes when you open this page.")

    df = get_attendance() if user.role == ROLE_ADMIN else get_attendance(user.username)
    scores: List[float] = list(st.session_state.get("match_scores_log") or [])

    c1, c2 = st.columns(2)
    with c1:
        fig = weekly_attendance_chart(df)
        if fig is None:
            empty_state("No trend data yet", "Attendance history will populate these charts.")
        else:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = recognition_accuracy_placeholder(scores[-40:])
        if fig2 is None:
            empty_state(
                "Match confidence trend",
                "Use **Attendance** to capture recognition attempts; scores aggregate for this session.",
            )
        else:
            st.plotly_chart(fig2, use_container_width=True)

    if user.role == ROLE_ADMIN and not df.empty and "username" in df.columns:
        st.markdown("#### Top members by check-ins (all time)")
        top = (
            df.groupby("username", as_index=False)
            .size()
            .rename(columns={"size": "check_ins"})
            .sort_values("check_ins", ascending=False)
            .head(12)
        )
        st.dataframe(top, use_container_width=True, hide_index=True, height=280)

    st.markdown("#### Recent activity")
    events = recent_events(30)
    act_df = events_to_activity_dataframe(events)
    if act_df.empty:
        empty_state("No activity", "System events will appear in this audit log.")
    else:
        st.dataframe(
            act_df,
            use_container_width=True,
            hide_index=True,
            height=min(400, 48 + len(act_df) * 36),
            column_config={
                "Time (UTC)": st.column_config.TextColumn("Time (UTC)", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Summary": st.column_config.TextColumn("Summary", width="large"),
                "Related member": st.column_config.TextColumn("Related member", width="small"),
            },
        )
