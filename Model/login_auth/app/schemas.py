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