from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Cookie, Depends, Header, HTTPException, status

from app.core.config import settings
from app.core.security import decode_jwt

def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2:
        return None
    if parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def get_current_claims(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.jwt_cookie_name),
) -> Dict[str, Any]:
    """Resolve JWT claims from the configured auth transport.

    Why this exists:
    - When using an API Gateway execute-api URL (no custom domain), cookies are cross-site and can be unreliable.
      In that case, use Authorization: Bearer <token>.
    - If the API is same-site with the frontend, cookies are fine.
    """

    token: Optional[str] = None

    if settings.auth_mode in ("bearer", "both"):
        token = _extract_bearer(authorization)

    if token is None and settings.auth_mode in ("cookie", "both"):
        token = cookie_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    claims = decode_jwt(token)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return claims


def require_admin(claims: Dict[str, Any] = Depends(get_current_claims)) -> Dict[str, Any]:
    if claims.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return claims
