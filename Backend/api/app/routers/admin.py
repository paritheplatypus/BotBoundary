from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from app.core.deps import require_admin
from app.schemas import AdminSessionRow
from app.services.db_service import DBService


router = APIRouter(prefix="/admin", tags=["admin"])
db = DBService()


@router.get("/sessions", response_model=List[AdminSessionRow])
def list_sessions(_: dict = Depends(require_admin), limit: int = 25):
    rows = db.list_recent_sessions(limit=limit)
    # Normalize keys
    out: List[AdminSessionRow] = []
    for r in rows:
        out.append(
            AdminSessionRow(
                session_id=r.get("sessionId"),
                user_id=r.get("userId"),
                status=r.get("status", "unknown"),
                ml_score=r.get("mlScore"),
                is_bot=r.get("isBot"),
                created_at=r.get("createdAt"),
            )
        )
    return out
