import sys
import os
import hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import SessionRequest, RiskResponse
from app.services.score_service import ScoreService
from app.services.feature_extractor import flatten_behavior
from app.models.autoencoder import AutoencoderModel
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str

MOCK_MODE = True

try:
    from Data.database import get_user_by_username, create_user, create_session, update_session_result
    DB_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Database unavailable ({e}). Running without persistence.")
    DB_AVAILABLE = False

app = FastAPI(title="CacheMeOutside - Behavioral Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("[STARTUP] Running in MOCK MODE - all logins will pass.")

score_svc = ScoreService()

@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": MOCK_MODE}

@app.post("/register")
def register_user(req: RegisterRequest):

    if not DB_AVAILABLE:
        raise HTTPException(status_code=500, detail="Database unavailable")

    # check if user already exists
    existing = get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    password_hash = hashlib.sha256(req.password.encode()).hexdigest()

    user = create_user(req.username, password_hash)

    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return {
        "message": "User created successfully",
        "userId": user["userId"]
    }

@app.post("/analyze", response_model=RiskResponse)
def analyze_session(request: SessionRequest):
    user_id = None
    session_id = None

    if DB_AVAILABLE:
        user = get_user_by_username(request.username)
        if user:
            user_id = user["userId"]
        if user_id:
            db_session = create_session(user_id)
            if db_session:
                session_id = db_session["sessionId"]

    model_output = {
        "model_name": "mock",
        "score": 0.01,
        "threshold": 0.05,
        "is_anomaly": False,
    }

    result = score_svc.process(model_output)
    result["session_id"] = session_id

    if DB_AVAILABLE and session_id and user_id:
        update_session_result(
            session_id=session_id,
            user_id=user_id,
            ml_score=result["risk_score"],
            is_bot=result["is_bot"],
        )

    return result