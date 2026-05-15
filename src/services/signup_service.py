"""Member self-registration with face enrollment."""

from __future__ import annotations

import io
from typing import List, Sequence

from PIL import Image

from src import auth
from src.activity_log import append_event
from src.config import DEFAULT_ADMIN_USERNAME
from src.register_user import delete_user_face_data, register_username_with_images
from src.utils import is_valid_password, is_valid_username


class SignupError(Exception):
    pass


def complete_signup(
    *,
    full_name: str,
    username: str,
    password: str,
    image_bytes_list: Sequence[bytes],
) -> auth.User:
    full_name = full_name.strip()
    if not full_name:
        raise SignupError("Full name is required.")
    if not is_valid_username(username):
        raise SignupError("Username must be 3–32 characters (letters, digits, ._-).")
    if username.lower() == DEFAULT_ADMIN_USERNAME.lower():
        raise SignupError("This username is reserved.")
    if not is_valid_password(password):
        raise SignupError("Password must be at least 6 characters.")
    if auth.user_exists(username):
        raise SignupError("Username already exists.")
    if not image_bytes_list:
        raise SignupError("Please provide at least one face image.")

    pil_images: List[Image.Image] = []
    for raw in image_bytes_list[:5]:
        pil_images.append(Image.open(io.BytesIO(raw)))

    try:
        user = auth.create_user(username, full_name, password, department="")
    except ValueError as exc:
        raise SignupError(str(exc)) from exc

    try:
        register_username_with_images(username, pil_images, replace_images=True)
    except Exception as exc:
        auth.delete_user(username)
        delete_user_face_data(username)
        raise SignupError(f"Face registration failed: {exc}") from exc

    append_event("user", "New self-registration", username=username)
    return user
