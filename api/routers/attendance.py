from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from api.deps import get_current_user, require_admin
from api.schemas import MarkAttendanceRequest, MarkAttendanceResponse
from api.routers.recognition import record_scores
from src import auth
from src.attendance_manager import attendance_csv_bytes, get_attendance, reset_attendance
from src.auth import ROLE_ADMIN, ROLE_USER
from src.activity_log import append_event
from src.services.attendance_service import mark_for_username, mark_from_boxes
from src.services.recognition_service import recognize_image_bytes
from src.services.reports_service import (
    dataframe_to_records,
    enrich_attendance_with_members,
    filter_reports,
    filtered_excel_bytes,
)
from src.services.settings_store import get_recognition_threshold

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("")
def list_attendance(
    user: auth.User = Depends(get_current_user),
    q: str = "",
    username: Optional[str] = None,
    department: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    today_only: bool = False,
) -> dict[str, Any]:
    users = auth.list_users()
    df_all = get_attendance()
    df = df_all if user.role == ROLE_ADMIN else get_attendance(user.username)
    enriched = enrich_attendance_with_members(df, users)
    view = filter_reports(
        enriched,
        q=q,
        username=username if user.role == ROLE_ADMIN else user.username,
        department=department if user.role == ROLE_ADMIN else None,
        date_from=date_from,
        date_to=date_to,
        today_only=today_only,
    )
    return {"records": dataframe_to_records(view), "total": len(view)}


@router.post("/mark", response_model=MarkAttendanceResponse)
def mark_attendance_body(
    body: MarkAttendanceRequest,
    user: auth.User = Depends(get_current_user),
) -> MarkAttendanceResponse:
    if not body.username:
        raise HTTPException(400, "username is required when marking without an image.")
    result = mark_for_username(user, body.username)
    return MarkAttendanceResponse(
        ok=result.ok,
        message=result.message,
        username=result.username,
        full_name=result.full_name,
        already_today=result.already_today,
    )


@router.post("/mark-from-image", response_model=MarkAttendanceResponse)
async def mark_from_image(
    image: UploadFile = File(...),
    user: auth.User = Depends(get_current_user),
) -> MarkAttendanceResponse:
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty image.")
    try:
        _, boxes = recognize_image_bytes(data, threshold=get_recognition_threshold())
    except Exception as exc:
        raise HTTPException(500, f"Recognition failed: {exc}") from exc
    record_scores(boxes)
    if not boxes:
        return MarkAttendanceResponse(ok=False, message="No face detected.")
    result = mark_from_boxes(user, boxes)
    return MarkAttendanceResponse(
        ok=result.ok,
        message=result.message,
        username=result.username,
        full_name=result.full_name,
        already_today=result.already_today,
    )


@router.get("/export/csv")
def export_csv(_: auth.User = Depends(get_current_user)) -> Response:
    return Response(
        content=attendance_csv_bytes(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_export.csv"},
    )


@router.get("/export/excel")
def export_excel(
    user: auth.User = Depends(get_current_user),
    q: str = "",
    username: Optional[str] = None,
    department: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    today_only: bool = False,
) -> Response:
    users = auth.list_users()
    df = get_attendance() if user.role == ROLE_ADMIN else get_attendance(user.username)
    enriched = enrich_attendance_with_members(df, users)
    view = filter_reports(
        enriched,
        q=q,
        username=username if user.role == ROLE_ADMIN else user.username,
        department=department if user.role == ROLE_ADMIN else None,
        date_from=date_from,
        date_to=date_to,
        today_only=today_only,
    )
    if view.empty:
        raise HTTPException(400, "No rows to export.")
    return Response(
        content=filtered_excel_bytes(view),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=attendance_filtered.xlsx"},
    )


@router.post("/reset")
def reset_log(admin: auth.User = Depends(require_admin)) -> dict[str, str]:
    reset_attendance()
    append_event("admin", "Attendance CSV reset", username=admin.username)
    return {"message": "Attendance log cleared."}
