"""Attendance marking rules (role-aware)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src import auth
from src.activity_log import append_event
from src.attendance_manager import already_marked_today, mark_attendance
from src.auth import ROLE_USER, User
from src.face_recognizer import FaceBoxResult
from src.services.recognition_service import primary_username


@dataclass
class MarkResult:
    ok: bool
    message: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    already_today: bool = False


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
            message=f"Attendance saved for {row.full_name}.",
            username=recognized_username,
            full_name=row.full_name,
        )
    return MarkResult(
        ok=False,
        message=f"{recognized_username} already marked today.",
        username=recognized_username,
        already_today=True,
    )
