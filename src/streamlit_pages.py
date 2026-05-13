"""Streamlit pages and navigation (UI layer — keeps business logic in ``src/``)."""

from __future__ import annotations

import io
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from src import auth
from src.auth import ROLE_ADMIN, ROLE_USER
from src.activity_log import append_event, recent_events
from src.analytics import recognition_accuracy_placeholder, weekly_attendance_chart
from src.attendance_manager import (
    attendance_csv_bytes,
    already_marked_today,
    get_attendance,
    mark_attendance,
    reset_attendance,
)
from src.utils import today_iso
from src.config import (
    BURST_DURATION_SEC,
    DEFAULT_ADMIN_USERNAME,
    LOGIN_LOCKOUT_SECONDS,
    MAX_LOGIN_ATTEMPTS,
    RECOGNITION_THRESHOLD,
    is_render_env,
)
from src.logger import get_logger
from src.pages.analytics import render_analytics
from src.recognition.burst_utils import pick_best_burst_result
from src.streamlit_session import (
    default_page_for_role,
    migrate_legacy_page,
    persist_auth_cookie,
    state_user,
    touch_activity,
    user_to_state,
)
from src.ui.components import (
    confirm_checkbox,
    empty_state,
    enrich_attendance_with_members,
    events_to_activity_dataframe,
    filter_reports_dataframe,
)
from src.ui.recognition_cards import render_recognition_summary
from src.ui.sidebar import NAV_ADMIN, NAV_USER, render_sidebar


# ---------------------------------------------------------------------------
# InsightFace warm-up (Streamlit resource cache)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading face recognition models…")
def _cached_face_app() -> object:
    from src.face_detector import get_face_app

    return get_face_app()


def _ensure_models() -> None:
    """Prime the InsightFace singleton once per process with a visible spinner."""
    _ = _cached_face_app()


# ---------------------------------------------------------------------------
# Small helpers (ported from legacy ``app.py``)
# ---------------------------------------------------------------------------
def _login_lock_key(username: str) -> str:
    return f"lockout:{username.lower()}"


def _is_locked(username: str) -> bool:
    until = float(st.session_state.get(_login_lock_key(username), 0.0))
    return until > time.time()


def _register_failed_attempt(username: str) -> None:
    key = f"fails:{username.lower()}"
    n = int(st.session_state.get(key, 0)) + 1
    st.session_state[key] = n
    if n >= MAX_LOGIN_ATTEMPTS:
        st.session_state[_login_lock_key(username)] = time.time() + LOGIN_LOCKOUT_SECONDS
        st.session_state[key] = 0


def _clear_failed_attempts(username: str) -> None:
    st.session_state[f"fails:{username.lower()}"] = 0
    st.session_state[_login_lock_key(username)] = 0.0


def _primary_username(boxes) -> str:
    from src.face_recognizer import FaceBoxResult

    matched = [b for b in boxes if isinstance(b, FaceBoxResult) and b.matched]
    if not matched:
        return "Unknown"
    best = max(matched, key=lambda b: b.score)
    return best.username


def _annotated_bgr(bgr: np.ndarray, boxes) -> np.ndarray:
    from src.camera import draw_face_overlay
    from src.face_recognizer import FaceBoxResult

    out = bgr
    for b in boxes:
        if not isinstance(b, FaceBoxResult):
            continue
        color = (0, 180, 0) if b.matched else (0, 80, 220)
        out = draw_face_overlay(out, b.bbox, b.username, b.score, color=color)
    return out


def _pil_to_bgr(pil: Image.Image) -> np.ndarray:
    import cv2

    rgb = np.array(pil.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _tail_logs(max_lines: int = 120) -> str:
    from src.config import LOGS_DIR

    path = LOGS_DIR / "app.log"
    if not path.exists():
        return "No log file yet — activity will appear here after the first events."
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"Unable to read logs: {exc}"
    return "\n".join(lines[-max_lines:])


# ---------------------------------------------------------------------------
# Auth pages
# ---------------------------------------------------------------------------
def page_login(cm) -> None:
    _, mid, _ = st.columns([1, 2.1, 1])
    with mid:
        # Do not split HTML across multiple st.markdown calls — Streamlit renders each as its
        # own block, which leaves an empty wrapper and looks like a white bar over the title.
        with st.container(border=True):
            st.markdown(
                '<div class="fa-login-brand">'
                '<p class="fa-login-product">FaceAttendance</p>'
                '<p class="fa-login-tagline">Intelligent recognition-based attendance</p>'
                '<p class="fa-login-sub">Secure check-ins for teams and institutions—face templates stay on this server.</p>'
                "</div>",
                unsafe_allow_html=True,
            )

            u = st.text_input("Username", key="login_username", placeholder="Enter your username")
            pw = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign in", type="primary", use_container_width=True, key="login_submit"):
                if not u or not pw:
                    st.error("Please enter both username and password.")
                elif _is_locked(u):
                    st.error("Too many invalid attempts — try again in a few minutes.")
                else:
                    try:
                        user = auth.authenticate(u, pw)
                    except LookupError:
                        st.error("Account not found. Create an account to continue.")
                        st.session_state["signup_redirect"] = True
                    else:
                        if user is None:
                            _register_failed_attempt(u)
                            st.error("Invalid username or password.")
                        else:
                            _clear_failed_attempts(u)
                            st.session_state.authenticated = True
                            st.session_state.user = user_to_state(user)
                            st.session_state["_cookie_restore_blocked_until"] = 0.0
                            touch_activity()
                            st.session_state.page = default_page_for_role(user.role)
                            persist_auth_cookie(cm)
                            append_event("auth", "User signed in", username=user.username)
                            st.toast("Signed in successfully.", icon="✓")
                            st.rerun()

            st.markdown('<p class="fa-muted">New member?</p>', unsafe_allow_html=True)
            if st.button("Create an account", use_container_width=True, key="goto_signup"):
                st.session_state.page = "signup"
                st.session_state.signup_step = 1
                st.session_state.signup_draft = {}
                st.rerun()

    if st.session_state.pop("signup_redirect", False):
        st.info("No account yet? Use **Create an account** above.")


def page_signup() -> None:
    if st.button("Back to sign in", key="signup_back"):
        st.session_state.page = "login"
        st.session_state.signup_step = 1
        st.session_state.signup_draft = {}
        st.rerun()

    step = int(st.session_state.get("signup_step") or 1)
    st.markdown("### Create member account")
    dots = "".join(
        '<span class="fa-step-dot active"></span>'
        if i + 1 == step
        else '<span class="fa-step-dot"></span>'
        for i in range(3)
    )
    st.markdown(
        f'<div class="fa-stepper">{dots} Step {step} of 3 · '
        f'{"Account" if step==1 else "Face photos" if step==2 else "Confirm"}</div>',
        unsafe_allow_html=True,
    )

    draft: Dict[str, Any] = dict(st.session_state.get("signup_draft") or {})

    if step == 1:
        full_name = st.text_input("Full name", value=draft.get("full_name", ""))
        username = st.text_input("Username", value=draft.get("username", ""))
        pw1 = st.text_input("Password", type="password")
        pw2 = st.text_input("Confirm password", type="password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Continue", type="primary", use_container_width=True):
                from src.utils import is_valid_password, is_valid_username

                if not full_name.strip():
                    st.error("Full name is required.")
                elif not is_valid_username(username):
                    st.error("Username must be 3–32 characters (letters, digits, ._-).")
                elif username.lower() == DEFAULT_ADMIN_USERNAME.lower():
                    st.error("This username is reserved.")
                elif not is_valid_password(pw1) or pw1 != pw2:
                    st.error("Passwords must match and be at least 6 characters.")
                elif auth.user_exists(username):
                    st.error("Username already exists.")
                else:
                    st.session_state.signup_draft = {
                        "full_name": full_name.strip(),
                        "username": username,
                        "pw": pw1,
                    }
                    st.session_state.signup_step = 2
                    st.rerun()
        with c2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.page = "login"
                st.session_state.signup_step = 1
                st.session_state.signup_draft = {}
                st.rerun()
        st.caption("Administrators are provisioned automatically — this flow is for members only.")
        return

    if step == 2:
        st.caption("Upload 1–5 clear, front-facing photos. Poor lighting reduces match quality.")
        files = st.file_uploader(
            "Face photos",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True):
                st.session_state.signup_step = 1
                st.rerun()
        with c2:
            if st.button("Review", type="primary", use_container_width=True):
                if not files:
                    st.error("Please upload at least one face image.")
                else:
                    st.session_state.signup_draft["files_meta"] = [f.name for f in files]
                    st.session_state.signup_file_bytes = [
                        (f.name, f.getvalue()) for f in files[:5]
                    ]
                    st.session_state.signup_step = 3
                    st.rerun()
        return

    # step 3 confirm
    d = dict(st.session_state.get("signup_draft") or {})
    st.write("**Account**")
    st.write(f"- Name: {d.get('full_name')}")
    st.write(f"- Username: `{d.get('username')}`")
    st.write(f"- Photos: {len(st.session_state.get('signup_file_bytes') or [])} file(s)")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Edit", use_container_width=True):
            st.session_state.signup_step = 1
            st.rerun()
    with c2:
        if st.button("Create account", type="primary", use_container_width=True):
            file_bytes = list(st.session_state.get("signup_file_bytes") or [])
            if not file_bytes:
                st.error("Missing uploads — go back to step 2.")
                return
            from src.register_user import register_username_with_images
            from src.utils import is_valid_password, is_valid_username

            username = str(d.get("username", ""))
            full_name = str(d.get("full_name", ""))
            pw1 = str(d.get("pw", ""))
            if not is_valid_username(username) or not is_valid_password(pw1):
                st.error("Session expired — restart signup.")
                return
            pil_images: List[Image.Image] = []
            for name, raw in file_bytes[:5]:
                pil_images.append(Image.open(io.BytesIO(raw)))

            try:
                auth.create_user(username, full_name.strip(), pw1, department="")
            except ValueError as exc:
                st.error(str(exc))
                return
            try:
                register_username_with_images(username, pil_images, replace_images=True)
            except Exception as exc:
                auth.delete_user(username)
                log.exception("Signup face registration failed: %s", exc)
                st.error(f"Face registration failed: {exc}")
                return
            append_event("user", "New self-registration", username=username)
            st.session_state.signup_step = 1
            st.session_state.signup_draft = {}
            st.session_state.signup_file_bytes = []
            st.session_state.page = "login"
            st.toast("Account created — you can sign in.", icon="✓")
            st.rerun()


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------
def page_admin_dashboard() -> None:
    user = state_user()
    if user is None or user.role != ROLE_ADMIN:
        st.error("You do not have access to this page.")
        return

    users = auth.list_users()
    clients = [u for u in users if u.role == ROLE_USER]
    total_users = len(clients)
    df = get_attendance()
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    present = (
        int(df.loc[df["date"].astype(str) == today, "username"].nunique())
        if not df.empty and "date" in df.columns
        else 0
    )
    absent = max(total_users - present, 0)
    scores: List[float] = list(st.session_state.get("match_scores_log") or [])
    avg_conf = float(sum(scores) / len(scores)) if scores else 0.0

    st.markdown("### Dashboard")
    st.caption("Operational overview — refreshed on each navigation.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total members", total_users)
    m2.metric("Present today", present)
    m3.metric("Absent (est.)", absent)
    m4.metric(
        "Avg. match confidence",
        f"{avg_conf:.1%}" if scores else "—",
        help="Rolling average of cosine similarity from recognition attempts this session.",
    )

    c1, c2 = st.columns((1.1, 1))
    with c1:
        fig = weekly_attendance_chart(df)
        if fig is None:
            st.info("Charts appear once attendance history exists.")
        else:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = recognition_accuracy_placeholder(scores[-25:])
        if fig2 is None:
            empty_state(
                "Recognition analytics",
                "Run attendance once to start collecting match confidence samples.",
            )
        else:
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Recent activity")
    events = recent_events(25)
    act_df = events_to_activity_dataframe(events)
    if act_df.empty:
        empty_state("No recent events", "Check-ins, registrations, and exports will appear in this log.")
    else:
        st.dataframe(
            act_df,
            use_container_width=True,
            hide_index=True,
            height=min(360, 42 + len(act_df) * 36),
            column_config={
                "Time (UTC)": st.column_config.TextColumn("Time (UTC)", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Summary": st.column_config.TextColumn("Summary", width="large"),
                "Related member": st.column_config.TextColumn("Related member", width="small"),
            },
        )


def page_user_dashboard() -> None:
    user = state_user()
    if user is None or user.role != ROLE_USER:
        st.error("You do not have access to this page.")
        return

    marked = already_marked_today(user.username)
    st.markdown("### My dashboard")
    c1, c2 = st.columns(2)
    c1.metric("Today's status", "Checked in" if marked else "Not checked in")
    c2.metric("Username", user.username)
    if marked:
        st.success("You are checked in for today.")
    else:
        st.info("You have not marked attendance yet today — open **Attendance** when ready.")


# ---------------------------------------------------------------------------
# Attendance capture
# ---------------------------------------------------------------------------
def page_attendance() -> None:
    import cv2

    from src.camera import iter_burst_frames, open_capture
    from src.register_user import validate_face_visible

    user = state_user()
    if user is None:
        st.error("Unauthorized.")
        return

    _ensure_models()

    st.markdown("### Mark attendance")
    threshold = float(st.session_state.get("recognition_threshold", RECOGNITION_THRESHOLD))
    st.caption(
        "Cosine similarity between enrolled templates and the live capture. "
        f"Current match threshold: **{threshold:.2f}**"
    )

    if "session_marks" not in st.session_state:
        st.session_state.session_marks = set()

    try:
        from src.face_recognizer import FaceBoxResult, recognize_all_faces
    except Exception as exc:  # pragma: no cover
        st.error(f"Recognition unavailable: {exc}")
        return

    def _record_scores(boxes) -> None:
        log_scores: List[float] = list(st.session_state.get("match_scores_log") or [])
        for b in boxes:
            if isinstance(b, FaceBoxResult):
                log_scores.append(float(b.score))
        st.session_state.match_scores_log = log_scores[-200:]

    def _maybe_mark(recognized_username: str, score: float) -> None:
        if recognized_username in ("Unknown", "", None):
            return
        if recognized_username in st.session_state.session_marks:
            st.toast(f"{recognized_username} already processed this session.", icon="ℹ️")
            return
        row = auth.get_user_by_username(recognized_username)
        if row is None:
            return
        if user.role == ROLE_USER and recognized_username != user.username:
            st.warning("Recognized a different person — not saved to your account.")
            return
        with st.spinner("Saving attendance…"):
            ok = mark_attendance(recognized_username, row.full_name)
        if ok:
            st.session_state.session_marks.add(recognized_username)
            append_event(
                "attendance",
                f"Member checked in: {row.full_name}",
                username=recognized_username,
            )
            st.toast(f"Attendance saved for {row.full_name}", icon="✓")
        else:
            st.toast(f"{recognized_username} already marked today.", icon="ℹ️")

    def _show_result(bgr, boxes: list) -> None:
        if not boxes:
            return
        st.image(cv2.cvtColor(_annotated_bgr(bgr, boxes), cv2.COLOR_BGR2RGB))
        best = max(boxes, key=lambda b: b.score)
        primary = _primary_username(boxes)
        mu = auth.get_user_by_username(primary) if primary != "Unknown" else None
        render_recognition_summary(
            matched_user=mu,
            display_username=best.username,
            confidence=float(best.score),
            matched=bool(best.matched),
            threshold=threshold,
        )

    if is_render_env():
        st.info(
            "Cloud deployment cannot access your local webcam. Use **Upload** with a clear selfie."
        )
        up = st.file_uploader("Upload a selfie or group photo", type=["png", "jpg", "jpeg"])
        if up:
            pil = Image.open(up)
            bgr = _pil_to_bgr(pil)
            with st.spinner("Detecting and matching faces…"):
                boxes = recognize_all_faces(bgr, threshold=threshold)
            _record_scores(boxes)
            if not boxes:
                st.warning("No face detected — try a closer, well-lit photo.")
            else:
                _show_result(bgr, boxes)
                if st.button("Confirm attendance for strongest match", type="primary"):
                    _maybe_mark(_primary_username(boxes), float(max(boxes, key=lambda b: b.score).score))
        return

    mode = st.radio(
        "Recognition mode",
        ["Upload", "Live camera", "Webcam burst"],
        horizontal=True,
        key="att_mode_local",
    )

    if mode == "Upload":
        up = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if up:
            pil = Image.open(up)
            bgr = _pil_to_bgr(pil)
            with st.spinner("Running recognition…"):
                boxes = recognize_all_faces(bgr, threshold=threshold)
            _record_scores(boxes)
            if not boxes:
                st.warning("No face detected in this image.")
            else:
                _show_result(bgr, boxes)
                if st.button("Save attendance from this image", type="primary"):
                    _maybe_mark(_primary_username(boxes), float(max(boxes, key=lambda b: b.score).score))
        return

    if mode == "Live camera":
        st.caption("Browser camera — hold steady for a second before capture.")
        cam = st.camera_input("Live camera")
        if cam is not None:
            pil = Image.open(cam)
            bgr = _pil_to_bgr(pil)
            if not validate_face_visible(bgr, min_score=0.28):
                st.warning("Face not clearly visible — improve lighting or move closer.")
            with st.spinner("Running recognition…"):
                boxes = recognize_all_faces(bgr, threshold=threshold)
            _record_scores(boxes)
            if not boxes:
                st.info("No faces detected — try again with a clearer view.")
            else:
                _show_result(bgr, boxes)
                if st.button("Save attendance from this frame", type="primary"):
                    _maybe_mark(_primary_username(boxes), float(max(boxes, key=lambda b: b.score).score))
        return

    # Webcam burst (OpenCV local camera)
    st.caption(
        f"Local OpenCV camera — captures about {BURST_DURATION_SEC:.1f}s "
        "of video, discards startup frames, then picks the best detection."
    )
    placeholder = st.empty()
    if st.button("Start webcam burst", type="primary"):
        try:
            cap = open_capture(0)
        except RuntimeError as exc:
            st.error(str(exc))
            return
        try:
            st.info("Warming up camera — stay centered, look at the lens.")
            frame_results: List[tuple] = []
            with st.spinner("Capturing and analyzing burst…"):
                for frame in iter_burst_frames(cap):
                    boxes = recognize_all_faces(frame, threshold=threshold)
                    _record_scores(boxes)
                    frame_results.append((frame, boxes))
                    placeholder.image(
                        cv2.cvtColor(_annotated_bgr(frame, boxes), cv2.COLOR_BGR2RGB),
                        channels="RGB",
                    )
            st.success(f"Processed {len(frame_results)} analyzed frames.")
            if not frame_results:
                st.error(
                    "No frames were captured. Close other apps using the camera and try again."
                )
                return
            bgr_best, boxes_best, pick_kind = pick_best_burst_result(frame_results)
            if bgr_best is None or not boxes_best:
                st.warning(
                    "No faces detected during the burst. Try brighter light, face the camera directly, "
                    "or lower the recognition threshold in **Settings**."
                )
                return
            if pick_kind == "unmatched_fallback":
                relaxed = max(0.22, threshold * 0.88)
                boxes_relaxed = recognize_all_faces(bgr_best, threshold=relaxed)
                _record_scores(boxes_relaxed)
                if any(b.matched for b in boxes_relaxed):
                    boxes_best = boxes_relaxed
                    pick_kind = "matched"
                st.caption(
                    f"No frame cleared the primary threshold ({threshold:.2f}); "
                    f"retried best frame at **{relaxed:.2f}**."
                )
            _show_result(bgr_best, boxes_best)
            primary = _primary_username(boxes_best)
            best = max(boxes_best, key=lambda b: b.score)
            if st.button("Confirm attendance from burst", type="primary"):
                _maybe_mark(primary, float(best.score))
        finally:
            cap.release()


# ---------------------------------------------------------------------------
# Admin — members
# ---------------------------------------------------------------------------
def page_admin_members() -> None:
    user = state_user()
    if user is None or user.role != ROLE_ADMIN:
        st.error("Unauthorized.")
        return

    _ensure_models()

    st.markdown("### Members")
    st.caption("Register members, assign units, and manage face templates.")

    with st.expander("Register a new member", expanded=True):
        with st.form("reg_user_form"):
            full_name = st.text_input("Full name", key="adm_reg_fn")
            username = st.text_input("Username", key="adm_reg_un")
            department = st.text_input("Department / unit (optional)", key="adm_reg_dept")
            pw1 = st.text_input("Temporary password", type="password", key="adm_reg_p1")
            pw2 = st.text_input("Confirm password", type="password", key="adm_reg_p2")
            up_files = st.file_uploader(
                "Face images",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="adm_reg_files",
            )
            submitted = st.form_submit_button("Create member + face template")
        if submitted:
            from src.utils import is_valid_password, is_valid_username
            from src.register_user import delete_user_face_data, register_username_with_images

            if not is_valid_username(username):
                st.error("Invalid username.")
            elif auth.user_exists(username):
                st.error("Username already exists.")
            elif not is_valid_password(pw1) or pw1 != pw2:
                st.error("Password issue — check length (6+) and confirmation.")
            elif not up_files:
                st.error("Upload at least one training image.")
            else:
                pil_list = [Image.open(f) for f in up_files[:5]]
                try:
                    auth.create_user(username, full_name.strip(), pw1, department=department)
                    register_username_with_images(username, pil_list, replace_images=True)
                except Exception as exc:
                    auth.delete_user(username)
                    delete_user_face_data(username)
                    st.error(str(exc))
                else:
                    append_event("user", f"Registered member {username}", username=username)
                    st.toast(f"Member `{username}` created.", icon="✓")

    users = auth.list_users()
    clients = [u for u in users if u.role == ROLE_USER]
    st.markdown("#### Directory")
    if not clients:
        empty_state(
            "No registered members",
            "Create the first member using the form above.",
        )
        return

    q = st.text_input("Search members", key="user_search")
    filtered = [
        u
        for u in clients
        if q.strip().lower() in u.username.lower()
        or q.strip().lower() in u.full_name.lower()
        or q.strip().lower() in (u.department or "").lower()
    ]
    from src.face_recognizer import has_embedding

    for u in filtered:
        cc1, cc2, cc3 = st.columns([3, 1.2, 1])
        cc1.markdown(f"**{u.username}**  \n{u.full_name}  \n_{u.department or '—'}_")
        cc2.caption("Face template OK" if has_embedding(u.username) else "Missing template")
        if cc3.button("Delete", key=f"del_{u.username}"):
            st.session_state.pending_delete_user = u.username
    pending = st.session_state.get("pending_delete_user")
    if pending:
        st.warning(f"Delete **{pending}**? This removes embeddings and images.")
        if confirm_checkbox("I understand this cannot be undone.", key="confirm_del_user"):
            if st.button("Confirm delete", type="primary", key="confirm_del_btn"):
                from src.register_user import delete_user_face_data

                auth.delete_user(pending)
                delete_user_face_data(pending)
                append_event("user", f"Deleted user {pending}", username=pending)
                st.session_state.pending_delete_user = None
                st.toast("User removed.", icon="✓")
                st.rerun()

    if not is_render_env():
        st.divider()
        st.caption("Local deployments can also capture training photos from the Attendance page burst flow.")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def page_reports() -> None:
    user = state_user()
    if user is None:
        st.error("Unauthorized.")
        return

    st.markdown("### Reports")
    st.caption("Search and filter attendance records. Use multiple words to narrow results.")

    users = auth.list_users()
    df_all = get_attendance()
    df = df_all if user.role == ROLE_ADMIN else get_attendance(user.username)
    enriched = enrich_attendance_with_members(df, users)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        q = st.text_input("Search", key="rep_search", placeholder="Name, member, department, date…")
    with c2:
        user_filter = None
        if user.role == ROLE_ADMIN:
            names = [""] + sorted(df_all["username"].dropna().unique().tolist()) if not df_all.empty else [""]
            pick = st.selectbox("Member", names, key="rep_user")
            user_filter = pick or None
    with c3:
        d_from = st.text_input("From (YYYY-MM-DD)", key="rep_from", placeholder="2026-01-01")
    with c4:
        d_to = st.text_input("To (YYYY-MM-DD)", key="rep_to", placeholder="2026-12-31")

    dept_filter = "(All)"
    today_only = False
    if user.role == ROLE_ADMIN and not enriched.empty and "department" in enriched.columns:
        depts = sorted(
            {str(x) for x in enriched["department"].dropna().unique() if str(x).strip()}
        )
        c5, c6 = st.columns([1.2, 1])
        with c5:
            dept_filter = st.selectbox(
                "Department / unit",
                ["(All)"] + depts,
                key="rep_dept",
            )
        with c6:
            today_only = st.checkbox("Today only", key="rep_today")
    elif user.role == ROLE_USER:
        today_only = st.checkbox("Today only", key="rep_today_user")

    view = filter_reports_dataframe(
        enriched,
        q=q,
        username=user_filter,
        department=dept_filter if user.role == ROLE_ADMIN else None,
        date_from=d_from or None,
        date_to=d_to or None,
        today_only=today_only,
        today_iso=today_iso(),
    )

    if view.empty:
        empty_state(
            "No matching records",
            "Try different search terms, clear filters, or record check-ins from **Attendance**.",
        )
    else:
        display_cols = [
            c
            for c in [
                "username",
                "full_name",
                "department",
                "date",
                "time",
                "record_status",
                "member_role",
            ]
            if c in view.columns
        ]
        show = view[display_cols] if display_cols else view
        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "username": st.column_config.TextColumn("Member", width="small"),
                "full_name": st.column_config.TextColumn("Name", width="medium"),
                "department": st.column_config.TextColumn("Department / unit", width="medium"),
                "date": st.column_config.TextColumn("Date", width="small"),
                "time": st.column_config.TextColumn("Time", width="small"),
                "record_status": st.column_config.TextColumn("Status", width="small"),
                "member_role": st.column_config.TextColumn("Role", width="small"),
            },
        )

    b1, b2 = st.columns(2)
    with b1:
        st.download_button(
            "Export full CSV",
            data=attendance_csv_bytes(),
            file_name=f"attendance_export_{pd.Timestamp.today().date()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with b2:
        if view.empty:
            st.caption("Excel export uses the filtered table — adjust filters to include rows.")
        else:
            xbuf = io.BytesIO()
            try:
                view.to_excel(xbuf, index=False, engine="openpyxl")
            except Exception as exc:  # pragma: no cover
                st.error(f"Excel export failed: {exc}")
            else:
                st.download_button(
                    "Export filtered Excel",
                    data=xbuf.getvalue(),
                    file_name=f"attendance_filtered_{pd.Timestamp.today().date()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def page_admin_settings() -> None:
    user = state_user()
    if user is None or user.role != ROLE_ADMIN:
        st.error("Unauthorized.")
        return

    st.markdown("### Settings")
    t1, t2 = st.tabs(["Recognition", "Security & data"])

    with t1:
        thresh = st.slider(
            "Recognition threshold",
            min_value=0.2,
            max_value=0.8,
            value=float(st.session_state.get("recognition_threshold", RECOGNITION_THRESHOLD)),
            step=0.01,
            help="Higher = stricter identity matches (cosine similarity).",
        )
        st.session_state["recognition_threshold"] = thresh

    with t2:
        st.divider()
        st.markdown("#### Administrator password")
        with st.form("admin_pw"):
            cur = st.text_input("Current password", type="password")
            new = st.text_input("New password", type="password")
            new2 = st.text_input("Confirm new password", type="password")
            submitted_pw = st.form_submit_button("Update password")
        if submitted_pw:
            verified = auth.authenticate(user.username, cur)
            if verified is None:
                st.error("Current password is incorrect.")
            elif len(new or "") < 6 or new != new2:
                st.error("New password invalid or does not match confirmation.")
            else:
                auth.change_password(user.username, new)
                st.toast("Password updated.", icon="✓")

        st.divider()
        st.markdown("#### Attendance data")
        st.caption("Reset clears all rows but keeps the CSV header.")
        if confirm_checkbox("I understand this permanently deletes attendance rows.", key="ack_reset"):
            if st.button("Reset attendance CSV", type="primary", key="reset_csv_btn"):
                reset_attendance()
                append_event("admin", "Attendance CSV reset")
                st.toast("Attendance log cleared.", icon="✓")
                st.rerun()

        st.divider()
        st.markdown("#### System logs (tail)")
        st.code(_tail_logs(), language="text")


def page_user_settings() -> None:
    user = state_user()
    if user is None or user.role != ROLE_USER:
        st.error("Unauthorized.")
        return

    st.markdown("### My profile")
    st.write(f"**Name:** {user.full_name}")
    st.write(f"**Username:** `{user.username}`")
    if user.department:
        st.write(f"**Department / unit:** {user.department}")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def render_authenticated_app(cm) -> None:
    user = state_user()
    if user is None:
        st.error("Session incomplete — please sign in again.")
        return

    if st.session_state.page in ("login", "signup"):
        st.session_state.page = default_page_for_role(user.role)
        st.rerun()

    touch_activity()
    render_sidebar(cm, user)
    persist_auth_cookie(cm)

    page = migrate_legacy_page(st.session_state.page, user.role)
    if user.role == ROLE_ADMIN and page.startswith("user_"):
        page = "admin_dashboard"
    elif user.role == ROLE_USER and page.startswith("admin_"):
        page = "user_dashboard"
    st.session_state.page = page

    allowed_admin = {k for _, k in NAV_ADMIN}
    allowed_user = {k for _, k in NAV_USER}
    allowed = allowed_admin if user.role == ROLE_ADMIN else allowed_user
    if page not in allowed:
        st.session_state.page = default_page_for_role(user.role)
        st.rerun()

    if page == "admin_dashboard":
        page_admin_dashboard()
    elif page == "user_dashboard":
        page_user_dashboard()
    elif page in ("admin_attendance", "user_attendance"):
        page_attendance()
    elif page == "admin_members":
        page_admin_members()
    elif page in ("admin_analytics", "user_analytics"):
        render_analytics()
    elif page in ("admin_reports", "user_reports"):
        page_reports()
    elif page == "admin_settings":
        page_admin_settings()
    elif page == "user_settings":
        page_user_settings()
    else:
        st.error("Unknown page.")
        st.session_state.page = default_page_for_role(user.role)


def render_public_app(cm) -> None:
    if st.session_state.page == "signup":
        page_signup()
    else:
        page_login(cm)
