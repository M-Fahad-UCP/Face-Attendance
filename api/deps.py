"""FastAPI dependencies: auth, roles."""

from __future__ import annotations

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src import auth
from src.auth import ROLE_ADMIN, User
from src.config import SESSION_COOKIE_NAME, SESSION_TIMEOUT_SECONDS
from src.session_cookie import issue_token, verify_token

_bearer = HTTPBearer(auto_error=False)


def user_to_out(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department or "",
    }


def create_session_token(user: User) -> str:
    return issue_token(user_id=user.id, ttl_seconds=SESSION_TIMEOUT_SECONDS)


def _user_from_token(token: Optional[str]) -> Optional[User]:
    if not token:
        return None
    uid = verify_token(token)
    if uid is None:
        return None
    return auth.get_user_by_id(uid)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    fa_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> User:
    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif fa_session:
        token = fa_session

    user = _user_from_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    fa_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Optional[User]:
    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif fa_session:
        token = fa_session
    return _user_from_token(token)
