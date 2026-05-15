"""Attendance marking rules (role-aware)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src import auth
from src.activity_log import append_event
from src.attendance_manager import (
    already_marked_today,
    get_today_record,
    has_checked_out_today,
    mark_attendance,
    mark_check_out,
    mark_manual_present,
)
from src.auth import ROLE_ADMIN, ROLE_USER, User
from src.face_recognizer import FaceBoxResult
from src.services.recognition_service import primary_username


@dataclass
class MarkResult:
    ok: bool
    message: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    already_today: bool = False
    checked_out: bool = False


@dataclass
class CheckoutResult:
    ok: bool
    message: str


def mark_from_boxes(actor: User, boxes: list[FaceBoxResult]) -> MarkResult:
    recognized = primary_username(boxes)
    if recognized in ("Unknown", "", None):
        return MarkResult(ok=False, message="No matched identity to mark.")
    return mark_for_username(actor, recognized)


def mark_for_username(actor: User, recognized_username: str) -> MarkResult:
    if recognized_username in ("Unknown", "", None):
        return MarkResult(ok=False, message="Invalid username.")

    row = auth.get_user_by_username(recognized_username)
    if row is None:
        return MarkResult(ok=False, message="User not found.")

    if actor.role == ROLE_USER and recognized_username != actor.username:
        return MarkResult(
            ok=False,
            message="Recognized a different person — not saved to your account.",
        )

    if already_marked_today(recognized_username):
        return MarkResult(
            ok=True,
            message=f"Already checked in today for {row.full_name}.",
            username=recognized_username,
            full_name=row.full_name,
            already_today=True,
            checked_out=has_checked_out_today(recognized_username),
        )

    ok = mark_attendance(recognized_username, row.full_name)
    if ok:
        append_event(
            "attendance",
            f"Member checked in: {row.full_name}",
            username=recognized_username,
        )
        return MarkResult(
            ok=True,
            message=f"Check-in saved for {row.full_name}.",
            username=recognized_username,
            full_name=row.full_name,
        )
    return MarkResult(
        ok=False,
        message=f"{recognized_username} could not be marked.",
        username=recognized_username,
    )


def _perform_checkout(username: str, *, via_signout: bool = False) -> bool:
    if not already_marked_today(username):
        return False
    if has_checked_out_today(username):
        return False
    row = auth.get_user_by_username(username)
    if not mark_check_out(username):
        return False
    name = row.full_name if row else username
    if via_signout:
        summary = f"Member checked out on sign-out: {name}"
    else:
        summary = f"Member checked out: {name}"
    append_event("attendance", summary, username=username)
    return True


def checkout_on_signout(user: User) -> bool:
    """Record check-out when a member signs out (best-effort)."""
    if user.role != ROLE_USER:
        return False
    return _perform_checkout(user.username, via_signout=True)


def checkout_user(actor: User, username: Optional[str] = None) -> CheckoutResult:
    target = username or actor.username
    if actor.role == ROLE_USER and target != actor.username:
        return CheckoutResult(ok=False, message="You can only check out for yourself.")
    if actor.role == ROLE_ADMIN:
        return CheckoutResult(ok=False, message="Administrators cannot check out.")

    if not already_marked_today(target):
        return CheckoutResult(ok=False, message="No check-in found for today.")
    if has_checked_out_today(target):
        return CheckoutResult(ok=False, message="Already checked out for today.")

    row = auth.get_user_by_username(target)
    if _perform_checkout(target):
        return CheckoutResult(
            ok=True,
            message=f"Check-out saved for {row.full_name if row else target}.",
        )
    return CheckoutResult(ok=False, message="Check-out failed.")


def admin_manual_mark(admin: User, username: str, reason: str) -> MarkResult:
    if admin.role != ROLE_ADMIN:
        return MarkResult(ok=False, message="Admin only.")
    row = auth.get_user_by_username(username)
    if row is None:
        return MarkResult(ok=False, message="User not found.")
    if already_marked_today(username):
        return MarkResult(
            ok=True,
            message=f"{username} already checked in today.",
            username=username,
            full_name=row.full_name,
            already_today=True,
        )
    if mark_manual_present(username, row.full_name, reason=reason):
        append_event(
            "admin",
            f"Manual attendance: {row.full_name} — {reason}",
            username=username,
        )
        return MarkResult(
            ok=True,
            message=f"Manual check-in recorded for {row.full_name}.",
            username=username,
            full_name=row.full_name,
        )
    return MarkResult(ok=False, message="Could not record manual attendance.")
