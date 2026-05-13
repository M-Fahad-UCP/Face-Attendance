"""
Streamlit dashboard sections (logic-free layout helpers).

Keeping heavy imports inside functions avoids slowing cold-start pages that
only need authentication.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.auth import User


def render_admin_summary(user: "User", registered: int, today_n: int) -> None:
    import streamlit as st

    st.subheader("Overview")
    st.markdown(
        f"**Signed in as:** `{user.username}` &nbsp;·&nbsp; **Role:** Administrator"
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Registered users", registered)
    c2.metric("Today's attendance rows", today_n)
    c3.metric("Known face templates", registered)


def render_user_summary(user: "User", today_marked: bool) -> None:
    import streamlit as st

    st.subheader("My overview")
    st.markdown(f"**{user.full_name}** (`{user.username}`)")
    st.success("You are checked in for today.") if today_marked else st.info(
        "You have not marked attendance yet today."
    )
