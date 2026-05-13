"""
Camera utilities for local (non-Render) environments.

OpenCV reads frames from the default webcam. We resize + skip frames to
keep CPU load low. Annotated frames are returned as BGR numpy arrays so
the UI can convert to RGB for Streamlit without cv2.imshow (compatible
with opencv-python-headless).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Generator, Optional

import cv2
import numpy as np

from src.config import (
    BURST_DURATION_SEC,
    BURST_FRAME_SKIP,
    BURST_MAX_WIDTH,
    BURST_WARMUP_READS,
    FRAME_SKIP,
    PROCESSING_FRAME_WIDTH,
)
from src.logger import get_logger

log = get_logger("camera")


@dataclass
class CameraConfig:
    device_index: int = 0
    frame_skip: int = FRAME_SKIP
    max_width: int = PROCESSING_FRAME_WIDTH


def _resize_keep_aspect(bgr: np.ndarray, max_width: int) -> np.ndarray:
    h, w = bgr.shape[:2]
    if w <= max_width:
        return bgr
    scale = max_width / float(w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def open_capture(device_index: int = 0) -> cv2.VideoCapture:
    """Open the default webcam. Raises RuntimeError if unavailable."""
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        log.error("Could not open webcam index %s", device_index)
        raise RuntimeError(
            "Webcam not found or permission denied. Check the device index "
            "and operating system privacy settings for camera access."
        )
    return cap


def grab_single_frame(
    cap: cv2.VideoCapture, max_width: int = PROCESSING_FRAME_WIDTH
) -> Optional[np.ndarray]:
    """Read one resized BGR frame, or None on failure."""
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return _resize_keep_aspect(frame, max_width)


def iter_resized_frames(
    cap: cv2.VideoCapture,
    *,
    max_frames: int,
    cfg: Optional[CameraConfig] = None,
) -> Generator[np.ndarray, None, None]:
    """
    Yield resized BGR frames, honouring FRAME_SKIP for CPU savings.

    Stops after ``max_frames`` read attempts (not every attempt yields —
    skipped frames are dropped entirely).
    """
    cfg = cfg or CameraConfig()
    for i in range(max_frames):
        ok, frame = cap.read()
        if not ok or frame is None:
            log.warning("Frame grab failed at read index %s", i)
            break
        if i % cfg.frame_skip != 0:
            continue
        yield _resize_keep_aspect(frame, cfg.max_width)


def iter_burst_frames(
    cap: cv2.VideoCapture,
    *,
    duration_sec: float = BURST_DURATION_SEC,
    warmup_reads: int = BURST_WARMUP_READS,
    frame_skip: int = BURST_FRAME_SKIP,
    max_width: int = BURST_MAX_WIDTH,
) -> Generator[np.ndarray, None, None]:
    """
    Time-based burst sampling for attendance.

    Discards the first ``warmup_reads`` successful grabs to avoid dark or
    unstable startup frames, then yields resized BGR frames until *duration_sec*
    elapses. Uses ``frame_skip`` of 1 by default for dense sampling.
    """
    t_end = time.time() + max(0.5, float(duration_sec))
    read_idx = 0
    yielded = 0
    while time.time() < t_end:
        ok, frame = cap.read()
        read_idx += 1
        if not ok or frame is None:
            log.warning("Burst read failed at index %s", read_idx)
            time.sleep(0.01)
            continue
        if read_idx <= warmup_reads:
            continue
        if (read_idx - warmup_reads) % max(1, frame_skip) != 0:
            continue
        yielded += 1
        yield _resize_keep_aspect(frame, max_width)
    log.info("Burst finished: reads=%s yielded=%s", read_idx, yielded)


def draw_face_overlay(
    bgr: np.ndarray,
    bbox_xyxy,
    label: str,
    score: float,
    color: tuple[int, int, int] = (0, 200, 0),
) -> np.ndarray:
    """Draw a rectangle + label on a copy of the frame."""
    out = bgr.copy()
    x1, y1, x2, y2 = [int(v) for v in bbox_xyxy]
    cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
    text = f"{label} ({score:.2f})"
    cv2.putText(
        out,
        text,
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )
    return out
