from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from api.deps import create_session_token, get_current_user, user_to_out
from api.schemas import LoginRequest, LoginResponse, MessageResponse, SignupJsonRequest, UserOut
from src import auth
from src.config import (
    SESSION_COOKIE_NAME,
    SESSION_TIMEOUT_SECONDS,
    is_production_env,
)
from src.activity_log import append_event
from src.services.attendance_service import checkout_on_signout
from src.services.login_guard import clear_failed_attempts, is_locked, register_failed_attempt
from src.services.signup_service import SignupError, complete_signup

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    prod = is_production_env()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=prod,
        samesite="none" if prod else "lax",
        max_age=SESSION_TIMEOUT_SECONDS,
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response) -> LoginResponse:
    username = body.username.strip()
    if not username or not body.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username and password required.")
    if is_locked(username):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts.")

    try:
        user = auth.authenticate(username, body.password)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found.")

    if user is None:
        register_failed_attempt(username)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password.")

    clear_failed_attempts(username)
    token = create_session_token(user)
    _set_session_cookie(response, token)
    return LoginResponse(user=UserOut(**user_to_out(user)), token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, user: auth.User = Depends(get_current_user)) -> MessageResponse:
    if checkout_on_signout(user):
        append_event("auth", "Signed out (check-out recorded)", username=user.username)
    else:
        append_event("auth", "Signed out", username=user.username)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return MessageResponse(message="Signed out.")


@router.get("/me", response_model=UserOut)
def me(user: auth.User = Depends(get_current_user)) -> UserOut:
    return UserOut(**user_to_out(user))


@router.post("/signup", response_model=MessageResponse)
async def signup(
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    images: list[UploadFile] = File(...),
) -> MessageResponse:
    try:
        raw_list = []
        for img in images[:5]:
            raw_list.append(await img.read())
        complete_signup(
            full_name=full_name,
            username=username.strip(),
            password=password,
            image_bytes_list=raw_list,
        )
    except SignupError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return MessageResponse(message="Account created — you can sign in.")

