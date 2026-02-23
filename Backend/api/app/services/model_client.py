from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings


class ModelClient:
    """HTTP client for the model inference service.

    The recommended deployment binds the model service to 127.0.0.1 on the same EC2 instance,
    so it is not exposed publicly. The backend calls it over loopback.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.model_url).rstrip("/")

    def analyze(
        self,
        features: List[float],
        registered_user: bool,
        user_id: Optional[str] = None,
        timeout_s: int = 5,
    ) -> Dict[str, Any]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if settings.model_api_key:
            headers["x-internal-api-key"] = settings.model_api_key

        payload: Dict[str, Any] = {
            "features": features,
            "registered_user": registered_user,
            "user_id": user_id,
        }

        resp = requests.post(
            f"{self.base_url}/analyze",
            json=payload,
            headers=headers,
            timeout=timeout_s,
        )
        resp.raise_for_status()
        return resp.json()
