"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    department: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user: UserOut
    token: str


class SignupJsonRequest(BaseModel):
    full_name: str
    username: str
    password: str


class MessageResponse(BaseModel):
    message: str
    ok: bool = True


class FaceBoxOut(BaseModel):
    bbox: List[float]
    username: str
    score: float
    matched: bool


class RecognizeResponse(BaseModel):
    faces: List[FaceBoxOut]
    primary_username: str
    threshold: float
    preview_base64: Optional[str] = None


class MarkAttendanceRequest(BaseModel):
    username: Optional[str] = None


class MarkAttendanceResponse(BaseModel):
    ok: bool
    message: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    already_today: bool = False


class SettingsOut(BaseModel):
    recognition_threshold: float


class ThresholdUpdate(BaseModel):
    recognition_threshold: float = Field(ge=0.2, le=0.8)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class TodayAttendanceRow(BaseModel):
    username: str
    full_name: str
    check_in_time: str
    check_out_time: str = ""
    checked_out: bool = False


class AdminDashboardOut(BaseModel):
    total_members: int
    present_today: int
    absent_estimate: int
    avg_match_confidence: Optional[float]
    recent_activity: List[dict[str, Any]]
    weekly_check_ins: List[dict[str, Any]]
    today_attendance: List[TodayAttendanceRow] = []


class UserDashboardOut(BaseModel):
    username: str
    full_name: str
    checked_in_today: bool
    checked_out_today: bool = False
    check_in_time: str = ""
    check_out_time: str = ""


class ManualMarkRequest(BaseModel):
    username: str
    reason: str = "Manual override"


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None


class AnalyticsOut(BaseModel):
    weekly_check_ins: List[dict[str, Any]]
    top_members: List[dict[str, Any]]
    recent_activity: List[dict[str, Any]]
    match_scores: List[float] = []


class MemberOut(BaseModel):
    id: int
    username: str
    full_name: str
    department: str
    has_face_template: bool
