"""SaaS-style sidebar: brand, role badge, nav buttons, sign out."""

from __future__ import annotations

from typing import List, Tuple

import streamlit as st

from src.activity_log import append_event
from src.auth import ROLE_ADMIN, User
from src.streamlit_session import touch_activity

NAV_ADMIN: List[Tuple[str, str]] = [
    ("Dashboard", "admin_dashboard"),
    ("Attendance", "admin_attendance"),
    ("Members", "admin_members"),
    ("Reports", "admin_reports"),
    ("Analytics", "admin_analytics"),
    ("Settings", "admin_settings"),
]

NAV_USER: List[Tuple[str, str]] = [
    ("Dashboard", "user_dashboard"),
    ("Attendance", "user_attendance"),
    ("Reports", "user_reports"),
    ("Analytics", "user_analytics"),
    ("Settings", "user_settings"),
]


def render_sidebar(cm, user: User) -> None:
    st.sidebar.markdown(
        '<div class="fa-sidebar-header"><span class="fa-sidebar-logo">FaceAttendance</span>'
        '<span class="fa-sidebar-tagline">Identity & attendance</span></div>',
        unsafe_allow_html=True,
    )
    role_label = "Administrator" if user.role == ROLE_ADMIN else "Member"
    st.sidebar.markdown(
        f'<div class="fa-sidebar-user"><span class="fa-role-pill">{role_label}</span>'
        f'<div class="fa-sidebar-username">{user.username}</div></div>',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="fa-nav-section">Navigation</div>', unsafe_allow_html=True)
    nav = NAV_ADMIN if user.role == ROLE_ADMIN else NAV_USER
    current = st.session_state.page
    for label, key in nav:
        is_active = current == key
        btn_key = f"nav_{key}"
        if is_active:
            st.sidebar.markdown(
                f'<div class="fa-nav-item fa-nav-active">{label}</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.sidebar.button(label, key=btn_key, use_container_width=True):
                st.session_state.page = key
                touch_activity()
                st.rerun()

    st.sidebar.markdown('<div class="fa-nav-divider"></div>', unsafe_allow_html=True)
    if st.sidebar.button("Sign out", key="logout_btn", use_container_width=True, type="primary"):
        from src.streamlit_session import logout

        logout(cm=cm, clear_cookie=True)
        append_event("auth", "Signed out", username=user.username)
        st.rerun()

    st.sidebar.markdown(
        '<div class="fa-session-note">Your session stays active securely on this device '
        "for a faster return next time.</div>",
        unsafe_allow_html=True,
    )
