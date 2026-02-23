from __future__ import annotations

from typing import Any, Dict, List, Optional

import sys
from pathlib import Path

# Ensure repository root is on PYTHONPATH so we can import the shared Data/ layer
ROOT = Path(__file__).resolve().parents[4]  # .../BotBoundary-main
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Data import database as db


class DBService:
    """Thin wrapper around the existing Data/database.py module."""

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        return db.get_user_by_username(username)

    def create_user(self, username: str, password_hash: str, role: str = "user") -> Optional[Dict[str, Any]]:
        return db.create_user(username=username, password_hash=password_hash, role=role)

    def create_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        return db.create_session(user_id=user_id)

    def update_session_result(
        self,
        session_id: str,
        user_id: str,
        ml_score: float,
        is_bot: bool,
        is_owner: Optional[bool] = None,
    ) -> bool:
        return db.update_session_result(session_id, user_id, ml_score=ml_score, is_bot=is_bot, is_owner=is_owner)

    def log_session_summary(self, session_id: str, summary: Dict[str, Any]) -> bool:
        # Stored as a single BehavioralEvents record (eventType=summary)
        return db.log_behavioral_event(session_id=session_id, event_type="summary", event_data={"summary": summary})

    def list_recent_sessions(self, limit: int = 25) -> List[Dict[str, Any]]:
        # DynamoDB query requires key; for a simple admin view we scan with a limit.
        try:
            resp = db.sessions_table.scan(Limit=limit)
            return resp.get("Items", [])
        except Exception:
            return []
