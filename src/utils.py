"""
Generic helpers shared across modules.

Kept dependency-light: only numpy + stdlib here.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np


# ---------------------------------------------------------------------------
# Cosine similarity (vectorised against a matrix of known embeddings)
# ---------------------------------------------------------------------------
def cosine_similarity(query: np.ndarray, gallery: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a single embedding and N gallery rows.

    InsightFace returns L2-normalised embeddings, but we re-normalise
    defensively so the function is correct even if callers pass raw vectors.

    Parameters
    ----------
    query : np.ndarray, shape (D,)
    gallery : np.ndarray, shape (N, D)

    Returns
    -------
    np.ndarray, shape (N,) with values in [-1.0, 1.0].
    """
    if gallery.size == 0:
        return np.empty((0,), dtype=np.float32)

    q = query.astype(np.float32, copy=False).ravel()
    g = gallery.astype(np.float32, copy=False)

    q_norm = np.linalg.norm(q) + 1e-10
    g_norm = np.linalg.norm(g, axis=1) + 1e-10

    return (g @ q) / (g_norm * q_norm)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def is_valid_username(value: str) -> bool:
    """Allow 3–32 chars: letters, digits, dot, dash, underscore."""
    return bool(_USERNAME_RE.match(value or ""))


def is_valid_password(value: str) -> bool:
    """Minimum 6 characters – simple but enforced."""
    return isinstance(value, str) and len(value) >= 6


def safe_filename(value: str) -> str:
    """Make a string safe for use as a filename / folder."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned or "user"


# ---------------------------------------------------------------------------
# Date / time
# ---------------------------------------------------------------------------
def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
def average_embeddings(vectors: Iterable[np.ndarray]) -> np.ndarray:
    """Average and L2-normalise a list of embeddings."""
    stacked = np.stack([v.astype(np.float32, copy=False) for v in vectors], axis=0)
    mean = stacked.mean(axis=0)
    mean /= np.linalg.norm(mean) + 1e-10
    return mean.astype(np.float32)


def list_embedding_files(embeddings_dir: Path) -> list[Path]:
    """Return every *.npy file in the embeddings folder."""
    if not embeddings_dir.exists():
        return []
    return sorted(embeddings_dir.glob("*.npy"))
