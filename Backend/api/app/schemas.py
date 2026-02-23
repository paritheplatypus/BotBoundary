from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class _Schema(BaseModel):
    # Allow fields like "model_used" without Pydantic namespace warnings.
    model_config = {"protected_namespaces": ()}


class RegisterRequest(_Schema):
    username: str = Field(min_length=3, max_length=256)
    password: str = Field(min_length=8, max_length=256)


class RegisterResponse(_Schema):
    user_id: str
    username: str


class LoginRequest(_Schema):
    username: str
    password: str
    behavior: Dict[str, Any]


class LoginResponse(_Schema):
    decision: str  # allow | challenge | deny
    session_id: str
    risk_score: float
    model_used: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None


class MeResponse(_Schema):
    user_id: str
    username: str
    role: str


class AdminSessionRow(_Schema):
    session_id: str
    user_id: str
    status: str
    ml_score: Optional[str] = None
    is_bot: Optional[bool] = None
    created_at: Optional[int] = None
