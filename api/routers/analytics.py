from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_current_user
from api.routers.recognition import get_match_scores
from api.schemas import AnalyticsOut
from src import auth
from src.attendance_manager import get_attendance
from src.auth import ROLE_ADMIN
from src.activity_log import recent_events
from src.services.dashboard_service import top_members_by_checkins, weekly_check_ins
from src.services.reports_service import events_to_rows

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsOut)
def analytics_summary(user: auth.User = Depends(get_current_user)) -> AnalyticsOut:
    df = get_attendance() if user.role == ROLE_ADMIN else get_attendance(user.username)
    top = top_members_by_checkins(df) if user.role == ROLE_ADMIN else []
    return AnalyticsOut(
        weekly_check_ins=weekly_check_ins(df),
        top_members=top,
        recent_activity=events_to_rows(recent_events(30)),
        match_scores=get_match_scores()[-40:],
    )
