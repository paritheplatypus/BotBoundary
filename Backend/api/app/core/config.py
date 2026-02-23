import os
from dataclasses import dataclass
from typing import List


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    # Server
    environment: str = os.getenv("ENVIRONMENT", "development")

    # CORS (Amplify domain(s) should be added here)
    cors_origins: List[str] = tuple(_split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173")))

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_ttl_minutes: int = int(os.getenv("JWT_TTL_MINUTES", "60"))
    jwt_cookie_name: str = os.getenv("JWT_COOKIE_NAME", "bb_auth")

    # DynamoDB
    aws_region: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    users_table_name: str = os.getenv("USERS_TABLE_NAME", "Users")
    sessions_table_name: str = os.getenv("SESSIONS_TABLE_NAME", "Sessions")
    behavioral_events_table_name: str = os.getenv("BEHAVIORAL_EVENTS_TABLE_NAME", "BehavioralEvents")

    # Model service (recommended: bind model to 127.0.0.1 so it is not public)
    model_url: str = os.getenv("MODEL_URL", "http://127.0.0.1:8001")
    model_api_key: str | None = os.getenv("MODEL_API_KEY")

    # Risk thresholds (backend business logic)
    # Risk score is normalized to 0..1. Higher means riskier.
    allow_threshold: float = float(os.getenv("ALLOW_THRESHOLD", "0.80"))
    challenge_threshold: float = float(os.getenv("CHALLENGE_THRESHOLD", "0.95"))


settings = Settings()
