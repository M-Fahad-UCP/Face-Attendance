from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user, require_admin
from api.schemas import MessageResponse, PasswordChangeRequest, SettingsOut, ThresholdUpdate
from src import auth
from src.activity_log import append_event
from src.config import LOGS_DIR
from src.services.settings_store import get_recognition_threshold, set_recognition_threshold

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(_: auth.User = Depends(get_current_user)) -> SettingsOut:
    return SettingsOut(recognition_threshold=get_recognition_threshold())


@router.patch("/threshold", response_model=SettingsOut)
def update_threshold(
    body: ThresholdUpdate,
    _: auth.User = Depends(require_admin),
) -> SettingsOut:
    val = set_recognition_threshold(body.recognition_threshold)
    return SettingsOut(recognition_threshold=val)


@router.post("/password", response_model=MessageResponse)
def change_password(
    body: PasswordChangeRequest,
    user: auth.User = Depends(get_current_user),
) -> MessageResponse:
    verified = auth.authenticate(user.username, body.current_password)
    if verified is None:
        raise HTTPException(400, "Current password is incorrect.")
    if len(body.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters.")
    auth.change_password(user.username, body.new_password)
    return MessageResponse(message="Password updated.")


@router.get("/logs")
def tail_logs(_: auth.User = Depends(require_admin)) -> dict[str, str]:
    path = LOGS_DIR / "app.log"
    if not path.exists():
        return {"logs": "No log file yet."}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return {"logs": f"Unable to read logs: {exc}"}
    return {"logs": "\n".join(lines[-120:])}
