"""
Signed browser cookie for Streamlit.

Streamlit's ``st.session_state`` resets on a full page refresh; a short-lived
HMAC-signed token in a cookie lets us restore the authenticated user into
session state on the next run (same pattern as many Streamlit production apps).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Optional

from src.config import SESSION_SIGNING_SECRET, USERS_DB_PATH


def _signing_key() -> bytes:
    secret = SESSION_SIGNING_SECRET or "face-attendance-dev-insecure-secret"
    material = f"{secret}|{USERS_DB_PATH}".encode("utf-8")
    return hashlib.sha256(material).digest()


def issue_token(*, user_id: int, ttl_seconds: int) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "uid": int(user_id),
        "iat": now,
        "exp": now + max(60, int(ttl_seconds)),
    }
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    sig = hmac.new(_signing_key(), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_token(token: str) -> Optional[int]:
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expected = hmac.new(_signing_key(), body.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        raw = base64.urlsafe_b64decode(body.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    uid = payload.get("uid")
    exp = payload.get("exp")
    if not isinstance(uid, int) or not isinstance(exp, (int, float)):
        return None
    if time.time() > float(exp):
        return None
    return int(uid)
