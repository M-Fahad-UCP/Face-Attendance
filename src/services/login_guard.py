"""In-memory login attempt tracking (replaces Streamlit session lockout keys)."""

from __future__ import annotations

import threading
import time
from typing import Dict, Tuple

from src.config import LOGIN_LOCKOUT_SECONDS, MAX_LOGIN_ATTEMPTS

_lock = threading.Lock()
_fails: Dict[str, int] = {}
_lockouts: Dict[str, float] = {}


def is_locked(username: str) -> bool:
    key = username.lower()
    with _lock:
        until = _lockouts.get(key, 0.0)
    return until > time.time()


def register_failed_attempt(username: str) -> None:
    key = username.lower()
    with _lock:
        n = _fails.get(key, 0) + 1
        _fails[key] = n
        if n >= MAX_LOGIN_ATTEMPTS:
            _lockouts[key] = time.time() + LOGIN_LOCKOUT_SECONDS
            _fails[key] = 0


def clear_failed_attempts(username: str) -> None:
    key = username.lower()
    with _lock:
        _fails.pop(key, None)
        _lockouts.pop(key, None)
