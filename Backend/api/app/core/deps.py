from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Cookie, Depends, HTTPException, status

from app.core.config import settings
from app.core.security import decode_jwt


def get_current_claims(token: Optional[str] = Cookie(default=None, alias=settings.jwt_cookie_name)) -> Dict[str, Any]:
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
