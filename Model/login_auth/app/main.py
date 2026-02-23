from __future__ import annotations

import os
from typing import Dict

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.schemas import RiskResponse, SessionRequest
from app.services.score_service import ScoreService
from app.models.autoencoder import AutoencoderModel
from app.models.ocsvm import OneClassSVMModel


app = FastAPI(title="BotBoundary Model Service")

score_service = ScoreService()


INTERNAL_API_KEY = os.getenv("MODEL_API_KEY")


def _require_internal_key(x_internal_api_key: str | None = Header(default=None)):
    if INTERNAL_API_KEY and x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")


# Cache models in-memory.
_autoencoder: AutoencoderModel | None = None
_ocsvm_cache: Dict[str, OneClassSVMModel] = {}


@app.on_event("startup")
def startup():
    global _autoencoder
    # The autoencoder input dimension is the feature vector length.
    # Default matches Backend/api/app/services/feature_vector.py.
    input_dim = int(os.getenv("FEATURE_DIM", "28"))
    _autoencoder = AutoencoderModel(input_dim=input_dim)
    _autoencoder.load()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze", response_model=RiskResponse, dependencies=[Depends(_require_internal_key)])
def analyze_session(request: SessionRequest):
    # Route the request.
    if request.registered_user:
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required when registered_user=true")

        model = _ocsvm_cache.get(request.user_id)
        if model is None:
            model = OneClassSVMModel(user_id=request.user_id)
            model.load()
            _ocsvm_cache[request.user_id] = model
    else:
        if _autoencoder is None:
            raise HTTPException(status_code=503, detail="Model not initialized")
        model = _autoencoder

    model_output = model.predict(request.features)
    final = score_service.process(model_output)
    return final
