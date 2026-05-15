"""Face detection, matching, and image helpers."""

from __future__ import annotations

import base64
import io
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from src.face_recognizer import FaceBoxResult, recognize_all_faces
from src.services.settings_store import get_recognition_threshold


def ensure_models() -> None:
    from src.face_detector import get_face_app

    get_face_app()


def pil_bytes_to_bgr(data: bytes) -> np.ndarray:
    pil = Image.open(io.BytesIO(data))
    rgb = np.array(pil.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def primary_username(boxes: List[FaceBoxResult]) -> str:
    matched = [b for b in boxes if b.matched]
    if not matched:
        return "Unknown"
    best = max(matched, key=lambda b: b.score)
    return best.username


def annotated_bgr(bgr: np.ndarray, boxes: List[FaceBoxResult]) -> np.ndarray:
    from src.camera import draw_face_overlay

    out = bgr
    for b in boxes:
        color = (0, 180, 0) if b.matched else (0, 80, 220)
        out = draw_face_overlay(out, b.bbox, b.username, b.score, color=color)
    return out


def recognize_image_bytes(
    data: bytes,
    *,
    threshold: Optional[float] = None,
) -> Tuple[np.ndarray, List[FaceBoxResult]]:
    ensure_models()
    thresh = get_recognition_threshold() if threshold is None else threshold
    bgr = pil_bytes_to_bgr(data)
    boxes = recognize_all_faces(bgr, threshold=thresh)
    return bgr, boxes


def boxes_to_dict(boxes: List[FaceBoxResult]) -> list[dict]:
    return [
        {
            "bbox": list(b.bbox),
            "username": b.username,
            "score": float(b.score),
            "matched": bool(b.matched),
        }
        for b in boxes
    ]


def bgr_to_base64_jpeg(bgr: np.ndarray, quality: int = 85) -> str:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("ascii")
