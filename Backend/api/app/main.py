from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, admin


app = FastAPI(title="BotBoundary API", version="1.0")


# CORS: allow the Amplify-hosted frontend to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=(settings.cors_allow_credentials or settings.auth_mode in ("cookie", "both")),
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
def health():
    return {"ok": True, "environment": settings.environment}


app.include_router(auth.router)
app.include_router(admin.router)
