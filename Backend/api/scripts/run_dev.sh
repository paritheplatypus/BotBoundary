#!/usr/bin/env bash
set -euo pipefail

# Local dev runner. Requires a valid AWS profile or local DynamoDB.

export ENVIRONMENT=development
export CORS_ORIGINS="http://localhost:5173"
export MODEL_URL="http://127.0.0.1:8001"

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
