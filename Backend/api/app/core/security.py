from __future__ import annotations

import time
from typing import Any, Dict, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings


# Argon2id password hashing (per project documentation)
_ph = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=64_000, # KiB (~64MB)
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_jwt(payload: Dict[str, Any], ttl_minutes: int | None = None) -> str:
    now = int(time.time())
    ttl = ttl_minutes if ttl_minutes is not None else settings.jwt_ttl_minutes
    claims = {
        **payload,
        "iat": now,
        "exp": now + int(ttl * 60),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
