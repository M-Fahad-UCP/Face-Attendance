from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from api.deps import require_admin
from src.activity_log import recent_events
from src.services.reports_service import events_to_rows

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(
    _: object = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
    kind: Optional[str] = None,
) -> dict[str, Any]:
    events = recent_events(limit * 2)
    if kind:
        events = [e for e in events if str(e.get("kind", "")) == kind]
    events = events[:limit]
    return {"events": events_to_rows(events), "total": len(events)}
