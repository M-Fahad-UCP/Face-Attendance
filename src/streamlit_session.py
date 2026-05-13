"""Session bootstrap, idle timeout, and signed cookie restoration."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import streamlit as st

from src import auth
from src.auth import ROLE_ADMIN, ROLE_USER, User
from src.config import (
    SESSION_COOKIE_NAME,
    SESSION_TIMEOUT_SECONDS,
)
from src.logger import get_logger
from src.session_cookie import issue_token, verify_token

log = get_logger("streamlit_session")


def user_to_state(u: User) -> Dict[str, Any]:
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role,
        "department": getattr(u, "department", "") or "",
    }


def state_user() -> Optional[User]:
    raw = st.session_state.get("user")
    if not raw:
        return None
    return User(
        id=int(raw["id"]),
        username=str(raw["username"]),
        full_name=str(raw["full_name"]),
        role=str(raw["role"]),
        department=str(raw.get("department") or ""),
    )


def default_page_for_role(role: str) -> str:
    return "admin_dashboard" if role == ROLE_ADMIN else "user_dashboard"


def migrate_legacy_page(page: Optional[str], role: str) -> str:
    """Map older page labels to new route ids."""
    legacy = {
        "Admin dashboard": "admin_dashboard",
        "User dashboard": "user_dashboard",
        "Register user": "admin_members",
        "admin_users": "admin_members",
        "Start attendance": "admin_attendance"
        if role == ROLE_ADMIN
        else "user_attendance",
        "Attendance viewer": "admin_reports" if role == ROLE_ADMIN else "user_reports",
        "My profile": "user_settings",
        "Login": "login",
        "Signup": "signup",
    }
    if not page:
        return default_page_for_role(role)
    return legacy.get(page, page)


def init_session_defaults() -> None:
    defaults = {
        "authenticated": False,
        "user": None,
        "page": "login",
        "last_activity": 0.0,
        "recognition_threshold": None,
        "session_marks": set(),
        "match_scores_log": [],
        "pending_delete_user": None,
        "signup_step": 1,
        "signup_draft": {},
        "signup_file_bytes": [],
        "_cookie_restore_blocked_until": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def touch_activity() -> None:
    st.session_state.last_activity = time.time()


def check_session_timeout(cm=None) -> None:
    if not st.session_state.get("authenticated"):
        return
    last = float(st.session_state.get("last_activity") or 0.0)
    if last and (time.time() - last) > SESSION_TIMEOUT_SECONDS:
        st.warning("Session expired — please sign in again.")
        logout(cm=cm, clear_cookie=True)


def logout(cm=None, *, clear_cookie: bool = True) -> None:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.last_activity = 0.0
    st.session_state.page = "login"
    st.session_state.session_marks = set()
    st.session_state.pending_delete_user = None
    st.session_state.signup_step = 1
    st.session_state.signup_draft = {}
    st.session_state.signup_file_bytes = []
    st.session_state.match_scores_log = []

    for wk in list(st.session_state.keys()):
        if wk.startswith("nav_") or wk in (
            "nav_main_radio",
            "login_username",
            "login_password",
            "login_submit",
            "att_mode_local",
            "att_mode_cloud",
        ):
            try:
                del st.session_state[wk]
            except KeyError:
                pass

    # Block cookie restore for several seconds — CookieManager delete is async;
    # without this the next rerun can still read the old token and re-open the dashboard.
    st.session_state["_cookie_restore_blocked_until"] = time.time() + 20.0

    log.info("User logged out.")
    if clear_cookie and cm is not None:
        for i in range(3):
            try:
                cm.delete(SESSION_COOKIE_NAME, key=f"fa_cookie_del_{time.time_ns()}_{i}")
            except Exception as exc:  # pragma: no cover
                log.warning("Cookie delete failed: %s", exc)


def persist_auth_cookie(cm) -> None:
    """Refresh sliding cookie for authenticated users."""
    user = state_user()
    if user is None or cm is None:
        return
    try:
        token = issue_token(user_id=user.id, ttl_seconds=SESSION_TIMEOUT_SECONDS)
        cm.set(
            SESSION_COOKIE_NAME,
            token,
            key="fa_cookie_set",
            max_age=float(SESSION_TIMEOUT_SECONDS),
            same_site="lax",
        )
    except Exception as exc:  # pragma: no cover
        log.warning("Cookie set failed: %s", exc)


def try_restore_session_from_cookie(cm) -> bool:
    """If a valid signed cookie exists, hydrate ``st.session_state``."""
    if st.session_state.get("authenticated"):
        return True
    blocked = float(st.session_state.get("_cookie_restore_blocked_until") or 0.0)
    if time.time() < blocked:
        return False
    if cm is None:
        return False
    try:
        raw = cm.get(SESSION_COOKIE_NAME)
    except Exception as exc:  # pragma: no cover
        log.warning("Cookie read failed: %s", exc)
        return False
    if not raw:
        return False
    uid = verify_token(str(raw))
    if uid is None:
        try:
            cm.delete(SESSION_COOKIE_NAME, key="fa_cookie_del_restore")
        except Exception:
            pass
        return False
    user = auth.get_user_by_id(uid)
    if user is None:
        try:
            cm.delete(SESSION_COOKIE_NAME, key="fa_cookie_del_missing_user")
        except Exception:
            pass
        return False
    st.session_state.authenticated = True
    st.session_state.user = user_to_state(user)
    st.session_state.page = migrate_legacy_page(
        st.session_state.get("page"), user.role
    )
    if st.session_state.page in ("login", "signup"):
        st.session_state.page = default_page_for_role(user.role)
    touch_activity()
    log.info("Session restored from cookie for %s", user.username)
    return True
