<<<<<<< Updated upstream
from pydantic import BaseModel
from typing import List, Optional

class SessionRequest(BaseModel):
    features: List[float]
    registered_user: bool
    user_id: Optional[str] = None

class RiskResponse(BaseModel):
    model_used: str
    risk_score: float
    threshold: float
    is_anomaly: bool
    raw_score: float
=======
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ── Existing schemas (kept for /analyze endpoint) ──────────────────────────

class SessionRequest(BaseModel):
    features: List[float]
    registered_user: bool

class RiskResponse(BaseModel):
    model: str
    risk_score: float


# ── New schemas for /login endpoint ────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    behavior: Dict[str, Any]


class LoginResponse(BaseModel):
    session_id: str
    is_bot: bool
    risk_score: float
    model_used: str
    registered_user: bool
>>>>>>> Stashed changes
