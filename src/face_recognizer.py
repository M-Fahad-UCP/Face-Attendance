"""
In-memory gallery of registered embeddings + matching logic.

The gallery is rebuilt lazily from disk and cached in memory. We keep one
NumPy matrix of shape (N, 512) and a parallel list of usernames so that
recognition is a single matrix-vector multiplication (O(N)).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from src.config import EMBEDDINGS_DIR, RECOGNITION_THRESHOLD
from src.logger import get_logger
from src.utils import cosine_similarity, list_embedding_files

log = get_logger("face_recognizer")


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RecognitionResult:
    username: str          # "Unknown" when no match passes the threshold
    score: float           # cosine similarity in [-1, 1]
    matched: bool          # score >= threshold


@dataclass(frozen=True)
class FaceBoxResult:
    """One detected face + identity hypothesis."""

    bbox: Tuple[float, float, float, float]
    username: str
    score: float
    matched: bool


# ---------------------------------------------------------------------------
# Gallery cache
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_matrix: Optional[np.ndarray] = None    # shape (N, 512), float32
_names: list[str] = []
_loaded = False


def _load_gallery() -> None:
    """Read every *.npy under database/embeddings/ into memory."""
    global _matrix, _names, _loaded

    files = list_embedding_files(EMBEDDINGS_DIR)
    if not files:
        _matrix = np.empty((0, 512), dtype=np.float32)
        _names = []
        _loaded = True
        log.info("Gallery is empty.")
        return

    rows: list[np.ndarray] = []
    names: list[str] = []
    dim: Optional[int] = None
    for path in files:
        try:
            vec = np.load(path).astype(np.float32, copy=False).ravel()
            if vec.size == 0:
                log.warning("Skipping empty embedding: %s", path.name)
                continue
            if dim is None:
                dim = int(vec.size)
            elif int(vec.size) != dim:
                log.warning("Skipping embedding with wrong dims: %s", path.name)
                continue
            vec /= np.linalg.norm(vec) + 1e-10
            rows.append(vec)
            names.append(path.stem)
        except Exception as exc:  # pragma: no cover
            log.warning("Skipping corrupted embedding %s: %s", path.name, exc)

    d = dim or 512
    _matrix = np.stack(rows, axis=0) if rows else np.empty((0, d), np.float32)
    _names = names
    _loaded = True
    log.info("Loaded %d embeddings into gallery.", len(_names))


def reload_gallery() -> None:
    """Force the gallery to be re-read from disk on next use."""
    global _loaded
    with _lock:
        _loaded = False


def _ensure_loaded() -> None:
    if _loaded:
        return
    with _lock:
        if not _loaded:
            _load_gallery()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def gallery_size() -> int:
    _ensure_loaded()
    return 0 if _matrix is None else _matrix.shape[0]


def known_usernames() -> list[str]:
    _ensure_loaded()
    return list(_names)


def recognize(embedding: np.ndarray,
              threshold: float = RECOGNITION_THRESHOLD) -> RecognitionResult:
    """
    Match a query embedding against the gallery.

    Returns ``Unknown`` when no row clears the threshold or when the
    gallery is empty.
    """
    _ensure_loaded()

    if _matrix is None or _matrix.shape[0] == 0:
        return RecognitionResult(username="Unknown", score=0.0, matched=False)

    sims = cosine_similarity(embedding, _matrix)
    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])

    if best_score >= threshold:
        return RecognitionResult(
            username=_names[best_idx], score=best_score, matched=True
        )
    return RecognitionResult(username="Unknown", score=best_score, matched=False)


def recognize_all_faces(
    bgr: np.ndarray,
    *,
    threshold: float = RECOGNITION_THRESHOLD,
) -> List[FaceBoxResult]:
    """
    Detect every face in a BGR frame and classify each independently.

    This is used for still images and short webcam bursts. It calls the
    InsightFace detector once, then reuses gallery matching for each crop.
    """
    from src.face_detector import detect_faces  # local import avoids cycles

    faces = detect_faces(bgr)
    out: List[FaceBoxResult] = []
    for face in faces:
        emb = getattr(face, "normed_embedding", None)
        if emb is None:
            emb = getattr(face, "embedding", None)
        if emb is None:
            continue
        emb = emb.astype(np.float32, copy=False).ravel()
        emb /= np.linalg.norm(emb) + 1e-10
        rec = recognize(emb, threshold=threshold)
        bbox = tuple(float(x) for x in getattr(face, "bbox", (0, 0, 0, 0)))
        out.append(
            FaceBoxResult(
                bbox=bbox,
                username=rec.username,
                score=rec.score,
                matched=rec.matched,
            )
        )
    return out


def save_embedding(username: str, embedding: np.ndarray) -> None:
    """Persist an embedding to disk and invalidate the cache."""
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    target = EMBEDDINGS_DIR / f"{username}.npy"
    vec = embedding.astype(np.float32, copy=False).ravel()
    vec /= np.linalg.norm(vec) + 1e-10
    np.save(target, vec)
    reload_gallery()
    log.info("Saved embedding for '%s' -> %s", username, target.name)


def delete_embedding(username: str) -> bool:
    target = EMBEDDINGS_DIR / f"{username}.npy"
    if target.exists():
        target.unlink()
        reload_gallery()
        log.info("Deleted embedding for '%s'.", username)
        return True
    return False


def has_embedding(username: str) -> bool:
    return (EMBEDDINGS_DIR / f"{username}.npy").exists()
