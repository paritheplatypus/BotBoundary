from __future__ import annotations

import os
import sys

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "/home/ubuntu/BotBoundary")

from app.core.security import hash_password, verify_password
from app.models.autoencoder import AutoencoderModel
from app.schemas import RegisterRequest, RiskResponse, SessionRequest
from app.services.score_service import ScoreService

MOCK_MODE = True

try:
    from Data.database import (
        create_session,
        create_user,
        get_recent_sessions,
        get_session,
        get_user_by_username,
        save_behavior_payload,
        update_session_result,
        update_user_password_hash,
    )

    DB_AVAILABLE = True
    print("[STARTUP] Database connected successfully.")
except Exception as exc:  # pragma: no cover - startup fallback
    print(f"[WARN] Database unavailable ({exc}). Running without persistence.")
    DB_AVAILABLE = False

try:
    autoencoder = AutoencoderModel()
    autoencoder.load()
    print("[STARTUP] Autoencoder loaded successfully.")
except Exception as exc:  # pragma: no cover - startup fallback
    print(f"[WARN] Could not load autoencoder: {exc}.")
    autoencoder = None

app = FastAPI(title="CacheMeOutside - Behavioral Auth API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

score_svc = ScoreService()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mock_mode": MOCK_MODE,
        "db": DB_AVAILABLE,
        "model": autoencoder is not None,
    }


@app.post("/register")
def register_user(req: RegisterRequest) -> dict:
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    username = req.username.strip()
    if get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        password_hash = hash_password(req.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = create_user(username, password_hash)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return {"message": "Account created successfully", "userId": user["userId"]}


@app.post("/analyze", response_model=RiskResponse)
def analyze_session(request: SessionRequest) -> dict:
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    username = request.username.strip()
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    stored_hash = user.get("passwordHash", "")
    is_valid, needs_rehash = verify_password(request.password, stored_hash)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if needs_rehash:
        try:
            upgraded_hash = hash_password(request.password)
            update_user_password_hash(user["userId"], upgraded_hash)
        except Exception as exc:  # pragma: no cover - auth should still succeed
            print(f"[WARN] Could not upgrade password hash for {user['userId']}: {exc}")

    user_id = user["userId"]
    session_id = None
    db_session = create_session(user_id)
    if db_session:
        session_id = db_session["sessionId"]

    behavior_dict = request.behavior.model_dump()

    if MOCK_MODE or autoencoder is None:
        model_output = {
            "model_name": "mock",
            "score": 0.01,
            "threshold": 0.05,
            "is_anomaly": False,
        }
    else:
        try:
            parsed = {}
            for group in ["interaction", "keyboard", "mouse", "timing"]:
                group_data = behavior_dict.get(group, {})
                if isinstance(group_data, dict):
                    parsed.update(group_data)
            model_output = autoencoder.predict(parsed)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Model inference failed: {exc}",
            ) from exc

    result = score_svc.process(model_output)
    result["session_id"] = session_id

    if session_id:
        update_session_result(
            session_id=session_id,
            user_id=user_id,
            ml_score=result["risk_score"],
            is_bot=result["is_bot"],
        )
        save_behavior_payload(session_id, user_id, behavior_dict)

    return result


@app.get("/sessions")
def get_sessions(limit: int = 20) -> dict:
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")
    return {"sessions": get_recent_sessions(limit=limit)}


@app.get("/sessions/{session_id}")
def get_session_detail(session_id: str) -> dict:
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session
