from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from api.routers.recognition import get_match_scores
from api.schemas import AdminDashboardOut, UserDashboardOut
from src import auth
from src.auth import ROLE_ADMIN
from src.attendance_manager import get_attendance
from src.services.dashboard_service import admin_dashboard, user_dashboard, weekly_check_ins

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=AdminDashboardOut)
def admin_view(user: auth.User = Depends(get_current_user)) -> AdminDashboardOut:
    if user.role != ROLE_ADMIN:
        raise HTTPException(403, "Admin only")
    base = admin_dashboard(match_scores=get_match_scores())
    base["weekly_check_ins"] = weekly_check_ins(get_attendance())
    return AdminDashboardOut(**base)


@router.get("/user", response_model=UserDashboardOut)
def user_view(user: auth.User = Depends(get_current_user)) -> UserDashboardOut:
    data = user_dashboard(user)
    return UserDashboardOut(**data)
