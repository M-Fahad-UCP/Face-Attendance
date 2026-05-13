"""Helpers for live webcam burst attendance (best-frame selection)."""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from src.face_recognizer import FaceBoxResult


def pick_best_burst_result(
    frame_results: List[Tuple[np.ndarray, List[FaceBoxResult]]],
) -> Tuple[Optional[np.ndarray], List[FaceBoxResult], str]:
    """
    From a list of (bgr_frame, boxes), pick the best frame for attendance.

    Prefers the frame whose strongest *matched* identity has the highest
    cosine score; if none matched, falls back to the frame with the highest
    raw similarity (may be below threshold).
    """
    best_matched: Optional[Tuple[float, np.ndarray, List[FaceBoxResult]]] = None
    best_any: Optional[Tuple[float, np.ndarray, List[FaceBoxResult]]] = None

    for bgr, boxes in frame_results:
        if not boxes:
            continue
        top = max(boxes, key=lambda b: float(b.score))
        if best_any is None or top.score > best_any[0]:
            best_any = (float(top.score), bgr, boxes)
        matched = [b for b in boxes if b.matched]
        if matched:
            mt = max(matched, key=lambda b: float(b.score))
            if best_matched is None or mt.score > best_matched[0]:
                best_matched = (float(mt.score), bgr, boxes)

    if best_matched is not None:
        _, bgr, boxes = best_matched
        return bgr, boxes, "matched"
    if best_any is not None:
        _, bgr, boxes = best_any
        return bgr, boxes, "unmatched_fallback"
    return None, [], "empty"
