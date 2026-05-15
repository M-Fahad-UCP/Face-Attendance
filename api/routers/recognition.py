from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.deps import get_current_user
from api.schemas import FaceBoxOut, RecognizeResponse
from src import auth
from src.services.recognition_service import (
    annotated_bgr,
    boxes_to_dict,
    bgr_to_base64_jpeg,
    primary_username,
    recognize_image_bytes,
)
from src.services.settings_store import get_recognition_threshold

router = APIRouter(prefix="/recognize", tags=["recognition"])

_match_scores: list[float] = []
_MAX_SCORES = 200


def record_scores(boxes) -> None:
    global _match_scores
    for b in boxes:
        _match_scores.append(float(b.score))
    _match_scores = _match_scores[-_MAX_SCORES:]


def get_match_scores() -> list[float]:
    return list(_match_scores)


@router.post("", response_model=RecognizeResponse)
async def recognize(
    image: UploadFile = File(...),
    include_preview: bool = True,
    _: auth.User = Depends(get_current_user),
) -> RecognizeResponse:
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty image.")
    threshold = get_recognition_threshold()
    try:
        bgr, boxes = recognize_image_bytes(data, threshold=threshold)
    except Exception as exc:
        raise HTTPException(500, f"Recognition failed: {exc}") from exc

    record_scores(boxes)
    preview = None
    if include_preview and boxes:
        ann = annotated_bgr(bgr, boxes)
        preview = bgr_to_base64_jpeg(ann)

    return RecognizeResponse(
        faces=[FaceBoxOut(**f) for f in boxes_to_dict(boxes)],
        primary_username=primary_username(boxes),
        threshold=threshold,
        preview_base64=preview,
    )
