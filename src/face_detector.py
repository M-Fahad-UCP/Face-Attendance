"""
Singleton wrapper around InsightFace's FaceAnalysis.

Loaded ONCE per process. Caching the model is the single biggest RAM win
on the Render free tier – we never want two copies of buffalo_sc in memory.

ML concept
----------
InsightFace performs:
  1. Face detection (SCRFD) – locates each face as a bounding box.
  2. Face alignment   – warps the crop to a canonical 112×112 patch.
  3. Embedding        – a small CNN maps the patch to a 512-d vector.
The output `embedding_norm` is already L2-normalised, so cosine similarity
between two embeddings equals their dot product.
"""

from __future__ import annotations

import threading
from typing import List, Optional

import numpy as np

from src.config import (
    INSIGHTFACE_CTX_ID,
    INSIGHTFACE_DET_SIZE,
    INSIGHTFACE_MODEL_NAME,
    INSIGHTFACE_PROVIDERS,
)
from src.logger import get_logger

log = get_logger("face_detector")

_app = None
_app_lock = threading.Lock()


def get_face_app():
    """
    Return a process-wide FaceAnalysis instance. Thread-safe lazy init.

    Models are auto-downloaded to ~/.insightface on first call.
    """
    global _app
    if _app is not None:
        return _app

    with _app_lock:
        if _app is not None:
            return _app

        try:
            # Imported lazily so that import-time of this module stays cheap;
            # Streamlit's import scanner shouldn't trigger an ONNX init.
            from insightface.app import FaceAnalysis
        except Exception as exc:  # pragma: no cover - import-time error
            log.exception("Failed to import insightface: %s", exc)
            raise

        preferred = INSIGHTFACE_MODEL_NAME
        fallbacks = ["buffalo_sc", "buffalo_s"]
        try_order = []
        for name in (preferred,) + tuple(fallbacks):
            if name not in try_order:
                try_order.append(name)

        last_error: Exception | None = None
        app = None
        for model_name in try_order:
            log.info(
                "Loading InsightFace model='%s' providers=%s det_size=%s",
                model_name,
                INSIGHTFACE_PROVIDERS,
                INSIGHTFACE_DET_SIZE,
            )
            try:
                app = FaceAnalysis(
                    name=model_name,
                    providers=INSIGHTFACE_PROVIDERS,
                )
                app.prepare(
                    ctx_id=INSIGHTFACE_CTX_ID,
                    det_size=INSIGHTFACE_DET_SIZE,
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                log.warning("InsightFace model '%s' failed: %s", model_name, exc)

        if app is None:
            log.exception("All InsightFace model candidates failed.")
            raise RuntimeError(
                "Face recognition model failed to load. Check internet access "
                "on first run (models download to ~/.insightface). "
                f"Last error: {last_error}"
            ) from last_error

        _app = app
        log.info("InsightFace ready (active pack=%s).", getattr(app, "name", "unknown"))
        return _app


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def detect_faces(bgr_image: np.ndarray) -> List:
    """
    Run detection + embedding on a BGR image. Returns the raw list of Face
    objects from InsightFace (each has .bbox, .det_score, .embedding, etc.).
    """
    app = get_face_app()
    return app.get(bgr_image)


def best_embedding(bgr_image: np.ndarray) -> Optional[np.ndarray]:
    """
    Return the embedding of the most confident detected face, or None if
    no face was found. Embedding is L2-normalised float32, shape (512,).
    """
    faces = detect_faces(bgr_image)
    if not faces:
        return None

    # `det_score` is the detector confidence in [0, 1].
    best = max(faces, key=lambda f: float(getattr(f, "det_score", 0.0)))

    emb = getattr(best, "normed_embedding", None)
    if emb is None:
        emb = best.embedding
        emb = emb / (np.linalg.norm(emb) + 1e-10)
    return emb.astype(np.float32, copy=False)
