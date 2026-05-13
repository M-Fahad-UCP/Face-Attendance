"""Recognition result layout — metric-style summary cards."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st

from src.auth import ROLE_ADMIN, User


def render_recognition_summary(
    *,
    matched_user: Optional[User],
    display_username: str,
    confidence: float,
    matched: bool,
    threshold: float,
) -> None:
    """Show a compact professional summary after a recognition attempt."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    role_label = (
        "Administrator"
        if matched_user and matched_user.role == ROLE_ADMIN
        else "Member"
    )
    dept = (matched_user.department if matched_user else "") or "—"
    name = matched_user.full_name if matched_user else "—"
    st.markdown('<div class="fa-result-card">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Matched name", name if matched else "No confident match")
    c2.metric("Username", display_username if display_username != "Unknown" else "—")
    c3.metric("Role", role_label if matched_user else "—")
    c4.metric("Department / unit", dept)
    c5.metric("Match confidence", f"{confidence:.1%}" if matched else f"{confidence:.1%} (below {threshold:.2f})")
    st.caption(f"Processed at {ts} · Cosine similarity vs enrolled templates")
    st.markdown("</div>", unsafe_allow_html=True)
