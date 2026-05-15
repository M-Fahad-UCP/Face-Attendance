from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image

from api.deps import get_current_user, require_admin, user_to_out
from api.schemas import MemberOut, MessageResponse, UserOut, UserProfileUpdate
from src import auth
from src.auth import User
from src.activity_log import append_event
from src.auth import ROLE_USER
from src.face_recognizer import has_embedding
from src.register_user import delete_user_face_data, register_username_with_images
from src.utils import is_valid_password, is_valid_username

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[MemberOut])
def list_members(_: User = Depends(require_admin)) -> list[MemberOut]:
    clients = [u for u in auth.list_users() if u.role == ROLE_USER]
    return [
        MemberOut(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            department=u.department or "",
            has_face_template=has_embedding(u.username),
        )
        for u in clients
    ]


@router.post("", response_model=MessageResponse)
async def create_member(
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    department: str = Form(""),
    images: list[UploadFile] = File(...),
    _: User = Depends(require_admin),
) -> MessageResponse:
    if not is_valid_username(username):
        raise HTTPException(400, "Invalid username.")
    if auth.user_exists(username):
        raise HTTPException(400, "Username already exists.")
    if not is_valid_password(password):
        raise HTTPException(400, "Password must be at least 6 characters.")
    if not images:
        raise HTTPException(400, "Upload at least one face image.")

    pil_list = []
    for f in images[:5]:
        raw = await f.read()
        pil_list.append(Image.open(io.BytesIO(raw)))

    try:
        auth.create_user(username, full_name.strip(), password, department=department)
        register_username_with_images(username, pil_list, replace_images=True)
    except Exception as exc:
        auth.delete_user(username)
        delete_user_face_data(username)
        raise HTTPException(400, str(exc)) from exc

    append_event("user", f"Registered member {username}", username=username)
    return MessageResponse(message=f"Member {username} created.")


@router.patch("/{username}", response_model=UserOut)
def update_member(
    username: str,
    body: UserProfileUpdate,
    _: User = Depends(require_admin),
) -> UserOut:
    if not auth.update_user_profile(
        username,
        full_name=body.full_name,
        department=body.department,
    ):
        raise HTTPException(404, "User not found or nothing to update.")
    append_event("user", f"Updated profile for {username}", username=username)
    row = auth.get_user_by_username(username)
    if row is None:
        raise HTTPException(404, "User not found.")
    return UserOut(**user_to_out(row))


@router.post("/{username}/face", response_model=MessageResponse)
async def admin_update_face(
    username: str,
    images: list[UploadFile] = File(...),
    _: User = Depends(require_admin),
) -> MessageResponse:
    if not auth.get_user_by_username(username):
        raise HTTPException(404, "User not found.")
    if not images:
        raise HTTPException(400, "Upload at least one face image.")
    pil_list = []
    for f in images[:5]:
        raw = await f.read()
        pil_list.append(Image.open(io.BytesIO(raw)))
    try:
        register_username_with_images(username, pil_list, replace_images=True)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    append_event("user", f"Face template updated for {username}", username=username)
    return MessageResponse(message="Face template updated.")


@router.post("/me/face", response_model=MessageResponse)
async def reenroll_my_face(
    images: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
) -> MessageResponse:
    if user.role != ROLE_USER:
        raise HTTPException(403, "Only members can update their face template here.")
    if not images:
        raise HTTPException(400, "Upload at least one face image.")
    pil_list = []
    for f in images[:5]:
        raw = await f.read()
        pil_list.append(Image.open(io.BytesIO(raw)))
    try:
        register_username_with_images(user.username, pil_list, replace_images=True)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    append_event("user", "Face template re-enrolled", username=user.username)
    return MessageResponse(message="Face photos updated successfully.")


@router.delete("/{username}", response_model=MessageResponse)
def delete_member(username: str, admin: User = Depends(require_admin)) -> MessageResponse:
    if not auth.delete_user(username):
        raise HTTPException(404, "User not found or cannot be deleted.")
    delete_user_face_data(username)
    append_event("user", f"Deleted user {username}", username=username)
    return MessageResponse(message="User removed.")
