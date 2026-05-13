"""
Face Attendance System — Streamlit entrypoint.

InsightFace is primed lazily when attendance / user pages open so cold starts
stay fast on Render's free tier.
"""

from __future__ import annotations

import streamlit as st
from extra_streamlit_components import CookieManager

from src import auth
from src.config import (
    RECOGNITION_THRESHOLD,
    SESSION_SIGNING_SECRET,
    ensure_directories,
    is_render_env,
)
from src.logger import get_logger
from src.streamlit_session import (
    check_session_timeout,
    init_session_defaults,
    try_restore_session_from_cookie,
)
from src.streamlit_pages import render_authenticated_app, render_public_app
from src.ui.styles import inject_global_styles

log = get_logger("app")


def main() -> None:
    st.set_page_config(
        page_title="FaceAttendance",
        page_icon="📷",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    ensure_directories()
    auth.init_db()

    if is_render_env() and not SESSION_SIGNING_SECRET:
        log.warning(
            "SESSION_SIGNING_SECRET is not set. Set it in Render environment variables "
            "so signed session cookies are not predictable."
        )

    cookie_manager = CookieManager(key="fa_cookie_manager_v1")

    init_session_defaults()
    if st.session_state.recognition_threshold is None:
        st.session_state.recognition_threshold = float(RECOGNITION_THRESHOLD)

    try_restore_session_from_cookie(cookie_manager)
    check_session_timeout(cookie_manager)

    inject_global_styles()

    if st.session_state.authenticated:
        render_authenticated_app(cookie_manager)
    else:
        if st.session_state.page not in ("login", "signup"):
            st.session_state.page = "login"
        render_public_app(cookie_manager)


if __name__ == "__main__":
    main()
