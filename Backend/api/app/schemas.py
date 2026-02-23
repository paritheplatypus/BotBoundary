from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=256)
    password: str = Field(min_length=8, max_length=256)


class RegisterResponse(BaseModel):
    user_id: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str
    behavior: Dict[str, Any]


class LoginResponse(BaseModel):
    decision: str  # allow | challenge | deny
    session_id: str
    risk_score: float
    model_used: str


class MeResponse(BaseModel):
    user_id: str
    username: str
    role: str


class AdminSessionRow(BaseModel):
    session_id: str
    user_id: str
    status: str
    ml_score: Optional[str] = None
    is_bot: Optional[bool] = None
    created_at: Optional[int] = None
