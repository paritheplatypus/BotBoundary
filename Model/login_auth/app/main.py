import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "/home/ubuntu/BotBoundary")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import SessionRequest, RiskResponse
from app.services.score_service import ScoreService
from app.services.feature_extractor import flatten_behavior
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


MOCK_MODE = True

try:
    from Data.database import (
        get_user_by_username,
        create_user,
        create_session,
        update_session_result,
        get_recent_sessions,
        get_session,
        save_behavior_payload,
        log_behavioral_event,
    )
    DB_AVAILABLE = True
    print("[STARTUP] Database connected successfully.")
except Exception as e:
    print(f"[WARN] Database unavailable ({e}). Running without persistence.")
    DB_AVAILABLE = False

app = FastAPI(title="CacheMeOutside - Behavioral Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if MOCK_MODE:
    print("[STARTUP] Running in MOCK MODE - all logins will pass.")

score_svc = ScoreService()


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": MOCK_MODE, "db": DB_AVAILABLE}


@app.post("/register")
def register_user(req: RegisterRequest):
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    existing = get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()

    user = create_user(req.username, password_hash)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return {"message": "Account created successfully", "userId": user["userId"]}


@app.post("/analyze", response_model=RiskResponse)
def analyze_session(request: SessionRequest):
    user_id = None
    session_id = None

    if DB_AVAILABLE:
        user = get_user_by_username(request.username)
        if not user:
            user = create_user(request.username, "placeholder")
        if user:
            user_id = user["userId"]
            if user_id:
                db_session = create_session(user_id)
                if db_session:
                    session_id = db_session["sessionId"]

    behavior_dict = request.behavior.model_dump()

    if MOCK_MODE:
        model_output = {
            "model_name": "mock",
            "score": 0.01,
            "threshold": 0.05,
            "is_anomaly": False,
        }
    else:
        try:
            feature_vector = flatten_behavior(behavior_dict)
            from app.models.autoencoder import AutoencoderModel
            autoencoder = AutoencoderModel()
            autoencoder.load()
            model_output = autoencoder.predict(feature_vector)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model inference failed: {e}")

    result = score_svc.process(model_output)
    result["session_id"] = session_id

    if DB_AVAILABLE and session_id and user_id:
        update_session_result(
            session_id=session_id,
            user_id=user_id,
            ml_score=result["risk_score"],
            is_bot=result["is_bot"],
        )
        save_behavior_payload(session_id, user_id, behavior_dict)
        log_behavioral_event(session_id, "behavior_payload", behavior_dict)

    return result


@app.get("/sessions")
def get_sessions(limit: int = 20):
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    sessions = get_recent_sessions(limit=limit)
    return {"sessions": sessions}


@app.get("/sessions/{session_id}")
def get_session_detail(session_id: str):
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session
