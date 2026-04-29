import hashlib
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "/home/ubuntu/BotBoundary")

from app.models.autoencoder import AutoencoderModel
from app.schemas import RiskResponse, SessionRequest
from app.services.score_service import ScoreService


class RegisterRequest(BaseModel):
    username: str
    password: str


MOCK_MODE = False

try:
    from Data.database import (
        create_session,
        create_user,
        get_recent_sessions,
        get_session,
        get_session_events,
        get_user_by_username,
        save_behavior_events,
        save_behavior_payload,
        update_session_result,
    )

    DB_AVAILABLE = True
    print("[STARTUP] Database connected successfully.")
except Exception as e:
    print(f"[WARN] Database unavailable ({e}). Running without persistence.")
    DB_AVAILABLE = False

try:
    autoencoder = AutoencoderModel()
    autoencoder.load()
    print("[STARTUP] Autoencoder loaded successfully.")
except Exception as e:
    print(f"[WARN] Could not load autoencoder: {e}.")
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
def health():
    return {
        "status": "ok",
        "mock_mode": MOCK_MODE,
        "db": DB_AVAILABLE,
        "model": autoencoder is not None,
    }


@app.post("/register")
def register_user(req: RegisterRequest):
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    if get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = create_user(req.username, hashlib.sha256(req.password.encode()).hexdigest())
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return {"message": "Account created successfully", "userId": user["userId"]}


@app.post("/analyze", response_model=RiskResponse)
def analyze_session(request: SessionRequest):
    user_id = None
    session_id = None
    registered = (
            request.username == "nolanpark"
    )

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
            model_name=result.get("model"),
            threshold=result.get("threshold"),
        )

        save_behavior_payload(session_id, user_id, behavior_dict)

        # This is the missing persistence path that caused BehavioralEvents to
        # stay empty in the current codebase.
        save_behavior_events(
            session_id=session_id,
            user_id=user_id,
            behavior=behavior_dict,
            inference={
                "model": result.get("model"),
                "risk_score": result.get("risk_score"),
                "threshold": result.get("threshold"),
                "is_bot": result.get("is_bot"),
            },
        )

    return result


@app.get("/sessions")
def get_sessions(limit: int = 20):
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")
    return {"sessions": get_recent_sessions(limit=limit)}


@app.get("/sessions/{session_id}")
def get_session_detail(session_id: str):
    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session["behaviorEvents"] = get_session_events(session_id)
    return session
