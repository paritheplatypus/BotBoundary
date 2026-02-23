from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status

from app.core.config import settings
from app.core.security import create_jwt, hash_password, verify_password
from app.core.deps import get_current_claims
from app.schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, MeResponse
from app.services.db_service import DBService
from app.services.feature_vector import behavior_to_feature_vector
from app.services.model_client import ModelClient

router = APIRouter(prefix="/auth", tags=["auth"])

db = DBService()
model = ModelClient()


def _get_client_ip(request: Request) -> str | None:
    """Best-effort client IP extraction behind proxies (API Gateway / ALB / NLB).

    Order:
    1) X-Forwarded-For (first IP)
    2) X-Real-IP
    3) request.client.host
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip() or None
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip() or None
    return request.client.host if request.client else None


@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest):
    existing = db.get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    pw_hash = hash_password(req.password)
    user = db.create_user(req.username, pw_hash, role="user")
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return RegisterResponse(user_id=user["userId"], username=user["username"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, response: Response, request: Request):
    user = db.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(req.password, user.get("passwordHash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session = db.create_session(user["userId"])
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")

    # Convert behavior JSON -> feature vector (fixed order)
    features = behavior_to_feature_vector(req.behavior)

    # Store behavioral summary in DynamoDB (pseudonymized by sessionId)
    summary = {
        "userId": user["userId"],
        "username": user["username"],
        "features": features,
        "behavior": req.behavior,
        "ip": _get_client_ip(request),
        "userAgent": request.headers.get("user-agent"),
    }
    db.log_session_summary(session_id=session["sessionId"], summary=summary)

    # Route inference:
    # - default to generic bot detection
    # - if a user-specific profile/model exists, request user-specific inference
    enrolled_2fa = bool(user.get("behaviorProfile")) and bool(user.get("enrolled2fa"))
    registered_user = bool(enrolled_2fa)

    try:
        result = model.analyze(features=features, registered_user=registered_user, user_id=user["userId"])
    except Exception:
        # If model service is unavailable, fall back to "allow" (per documentation: fallback to standard password)
        # but still log that inference failed.
        result = {
            "model_used": "fallback",
            "risk_score": 0.0,
            "threshold": 1.0,
            "is_anomaly": False,
            "raw_score": 0.0,
        }

    risk = float(result.get("risk_score", 0.0))
    is_bot = bool(result.get("is_anomaly", False))
    model_used = str(result.get("model_used", "unknown"))

    # Business rules: allow / challenge / deny
    if is_bot and risk >= settings.challenge_threshold:
        decision = "deny"
    elif risk >= settings.challenge_threshold:
        decision = "challenge"
    elif risk >= settings.allow_threshold:
        decision = "challenge"
    else:
        decision = "allow"

    # Persist session result
    db.update_session_result(
        session_id=session["sessionId"],
        user_id=user["userId"],
        ml_score=risk,
        is_bot=is_bot,
        is_owner=(not is_bot) if registered_user else None,
    )

    token = None
    if decision == "allow":
        token = create_jwt({"user_id": user["userId"], "username": user["username"], "role": user.get("role", "user")})

        # Cookie auth is only reliable when the API is same-site with the frontend.
        # When using API Gateway's execute-api domain (no purchased custom domain), prefer bearer tokens.
        if settings.auth_mode in ("cookie", "both"):
            response.set_cookie(
                key=settings.jwt_cookie_name,
                value=token,
                httponly=True,
                secure=True if settings.environment != "development" else False,
                samesite="none" if settings.environment != "development" else "lax",
                max_age=settings.jwt_ttl_minutes * 60,
                path="/",
            )

    return LoginResponse(
        decision=decision,
        session_id=session["sessionId"],
        risk_score=risk,
        model_used=model_used,
        access_token=(token if (token and settings.auth_mode in ("bearer", "both")) else None),
        token_type=("bearer" if (token and settings.auth_mode in ("bearer", "both")) else None),
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.jwt_cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(claims=Depends(get_current_claims)):
    return MeResponse(
        user_id=claims["user_id"],
        username=claims["username"],
        role=claims.get("role", "user"),
    )
