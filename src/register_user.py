"""
Face registration orchestration.

Combines InsightFace embeddings with lightweight on-disk storage:
- ``database/embeddings/<username>.npy`` — single averaged template
- ``database/images/<username>/`` — a few small JPEGs for audit/debug

ML concept
----------
Multiple face crops from different poses/lighting are mapped to the same
512-D identity space. Averaging L2-normalised embeddings acts like a
simple prototype classifier centre — cheap and robust for tiny galleries.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List, Sequence

import cv2
import numpy as np
from PIL import Image

from src.config import IMAGES_DIR, REGISTRATION_CAPTURES
from src.face_detector import best_embedding, detect_faces
from src.face_recognizer import delete_embedding, save_embedding
from src.logger import get_logger
from src.utils import average_embeddings, safe_filename

log = get_logger("register_user")


def user_image_dir(username: str) -> Path:
    """Per-user folder under database/images/."""
    return IMAGES_DIR / safe_filename(username)


def clear_user_images(username: str) -> None:
    folder = user_image_dir(username)
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


def _compress_bgr_to_jpeg(bgr: np.ndarray, quality: int = 82) -> None:
    """In-place side effect helper — returns encoded bytes via imencode."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ok, buf = cv2.imencode(".jpg", bgr, encode_param)
    if not ok:
        raise ValueError("Failed to encode JPEG.")


def save_reference_jpeg(username: str, bgr: np.ndarray, index: int) -> Path:
    """Write a small JPEG for auditing; keeps disk usage low."""
    folder = user_image_dir(username)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"ref_{index:02d}.jpg"
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    if not ok:
        raise ValueError("JPEG compression failed.")
    path.write_bytes(buf.tobytes())
    return path


def embedding_from_bgr_images(images: Sequence[np.ndarray]) -> np.ndarray:
    """
    Require at least one valid face embedding across all images.

    Raises ValueError with a user-friendly message on failure.
    """
    vectors: List[np.ndarray] = []
    for idx, bgr in enumerate(images):
        emb = best_embedding(bgr)
        if emb is None:
            raise ValueError(f"No clear face detected in sample #{idx + 1}.")
        vectors.append(emb)
    return average_embeddings(vectors)


def embedding_from_uploaded_images(
    pil_images: Iterable[Image.Image],
    *,
    min_samples: int = 1,
    max_samples: int = REGISTRATION_CAPTURES,
) -> np.ndarray:
    """Convert uploaded PIL images to BGR numpy arrays and average."""
    rgbs: List[np.ndarray] = []
    for pil in pil_images:
        rgb = np.array(pil.convert("RGB"))
        rgbs.append(rgb)
        if len(rgbs) >= max_samples:
            break
    if len(rgbs) < min_samples:
        raise ValueError("Please provide at least one face image.")

    bgrs = [cv2.cvtColor(im, cv2.COLOR_RGB2BGR) for im in rgbs]
    return embedding_from_bgr_images(bgrs)


def register_username_with_images(
    username: str,
    pil_images: Iterable[Image.Image],
    *,
    replace_images: bool = True,
) -> None:
    """
    Persist embedding + optional JPEG references for *username*.

    ``replace_images`` wipes any previous JPEG folder for a clean slate.
    """
    if replace_images:
        clear_user_images(username)

    pil_list = list(pil_images)
    emb = embedding_from_uploaded_images(pil_list)
    save_embedding(username, emb)

    for i, pil in enumerate(pil_list[:REGISTRATION_CAPTURES]):
        rgb = np.array(pil.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        save_reference_jpeg(username, bgr, i)

    log.info("Registered face template for '%s'.", username)


def validate_face_visible(bgr: np.ndarray, *, min_score: float = 0.35) -> bool:
    """Return True if at least one confident face is present."""
    try:
        faces = detect_faces(bgr)
    except Exception as exc:  # pragma: no cover - model errors surfaced in UI
        log.warning("Face visibility check failed: %s", exc)
        return False
    if not faces:
        return False
    best = max(faces, key=lambda f: float(getattr(f, "det_score", 0.0)))
    return float(getattr(best, "det_score", 0.0)) >= min_score


def delete_user_face_data(username: str) -> None:
    """Remove embedding file + cropped JPEGs."""
    delete_embedding(username)
    clear_user_images(username)
