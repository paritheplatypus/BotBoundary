from pydantic import BaseModel
from typing import List

class SessionRequest(BaseModel):
    features: List[float]
    registered_user: bool

class RiskResponse(BaseModel):
    model: str
    risk_score: float