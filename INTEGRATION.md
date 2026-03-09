# BotBoundary — Integration & Deployment Guide
**CacheMeOutside Capstone Project**

---

## Architecture Overview

```
Browser (React/Vite)
  │  behaviorTracker.js collects mouse, keyboard, timing, interaction data
  │
  │  POST /analyze  { username, behavior, registered_user }
  ▼
FastAPI Backend  (Python)
  │  feature_extractor.py  → flatten nested behavior dict → List[float]
  │  model_router.py       → pick AutoEncoder (new user) or OCSVM (registered user)
  │  model.predict()       → risk score + is_bot verdict
  │  score_service.py      → format response
  │  database.py           → save session + result to DynamoDB
  │
  │  JSON { model, risk_score, threshold, is_bot, session_id }
  ▼
Browser
  └─ shows ✅ Human verified  OR  🚫 Suspicious activity detected
```

---

## What Was Integrated

| File | Change |
|------|--------|
| `FrontEnd/src/components/LoginForm.jsx` | Now POSTs behavior payload to `/analyze` instead of console.logging |
| `FrontEnd/src/styles/login.css` | Added result banner styles |
| `FrontEnd/.env` | Added `VITE_API_URL` config |
| `Model/login_auth/app/schemas.py` | Replaced flat `List[float]` schema with nested behavior struct matching frontend |
| `Model/login_auth/app/services/feature_extractor.py` | **New** — flattens behavior dict → 24-feature vector |
| `Model/login_auth/app/services/model_router.py` | Fixed `user_id` bug; added OCSVM per-user caching |
| `Model/login_auth/app/services/score_service.py` | Fixed response key names to match `RiskResponse` schema |
| `Model/login_auth/app/models/autoencoder.py` | Fixed `input_dim` default; imports `FEATURE_DIM` from extractor |
| `Model/login_auth/app/main.py` | Full rewrite: CORS, DB integration, feature extraction, fallback logic |

---

## Local Development Setup

### 1. Backend (FastAPI)

```bash
cd Model/login_auth

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# AWS credentials (needed for DynamoDB — skip if not set up yet)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Start the server
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` to see the auto-generated API docs.

> **Note:** The server starts even without trained models or a DB connection.
> It will log warnings but won't crash. Models must be trained before
> inference returns meaningful scores (see Training section below).

---

### 2. Frontend (React/Vite)

```bash
cd FrontEnd

npm install
npm run dev
```

Visit `http://localhost:5173` — the login page will appear.

---

## Training the Models

Before inference works, you need trained model artifacts.

### Autoencoder (for new/unknown users)

```bash
cd Model/login_auth
python training/train_autoencoder.py
```

This should output:
- `saved_models/autoencoder/autoencoder.pt`
- `saved_models/autoencoder/scaler.pkl`
- `saved_models/autoencoder/threshold.npy`

### One-Class SVM (per registered user)

```bash
cd Model/login_auth
python training/train_ocsvm.py --user_id <user_uuid>
```

This should output:
- `saved_models/user/user_<user_uuid>/ocsvm.pkl`
- `saved_models/user/user_<user_uuid>/scaler.pkl`

---

## Feature Vector Reference

`feature_extractor.py` produces a **24-dimensional** float vector in this order:

| Index | Feature | Source |
|-------|---------|--------|
| 0–8 | Mouse: total_moves, total_distance, normalized_distance, mean_speed, speed_std, max_speed, direction_changes, pause_count, movement_entropy | `mouse` |
| 9–15 | Keyboard: total_keystrokes, mean_interval_ms, interval_std_ms, min_interval_ms, max_interval_ms, backspace_ratio, paste_detected | `keyboard` |
| 16–20 | Interaction: click_count, scroll_count, focus_changes, mouse_keyboard_ratio, interaction_rate | `interaction` |
| 21–23 | Timing: session_duration_ms, time_to_first_action_ms, idle_time_ratio | `timing` |

> **Important:** Your training scripts must use this same feature order.
> Import `FEATURE_ORDER` and `FEATURE_DIM` from `feature_extractor.py` in your training code.

---

## DynamoDB Setup (AWS)

The backend uses three tables. Create them in the AWS Console or via CLI:

```bash
# Users table
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Sessions table
aws dynamodb create-table \
  --table-name Sessions \
  --attribute-definitions AttributeName=sessionId,AttributeType=S AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=sessionId,KeyType=HASH AttributeName=userId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

# BehavioralEvents table
aws dynamodb create-table \
  --table-name BehavioralEvents \
  --attribute-definitions AttributeName=sessionId,AttributeType=S AttributeName=timestamp,AttributeType=N \
  --key-schema AttributeName=sessionId,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

Add a GSI on Sessions for querying by userId:
```bash
aws dynamodb update-table \
  --table-name Sessions \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --global-secondary-index-updates \
    "[{\"Create\":{\"IndexName\":\"userId-index\",\"KeySchema\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}}]" \
  --billing-mode PAY_PER_REQUEST
```

---

## Deployment

### Option A — Free Tier (Recommended for capstone demo)

**Backend → Render.com**

1. Push your repo to GitHub
2. Create a new "Web Service" on [render.com](https://render.com)
3. Set:
   - Root directory: `Model/login_auth`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`

**Frontend → Vercel**

1. Create a new project on [vercel.com](https://vercel.com)
2. Set:
   - Root directory: `FrontEnd`
   - Build command: `npm run build`
   - Output directory: `dist`
3. Add environment variable: `VITE_API_URL=https://your-render-backend.onrender.com`

**Total cost: $0** (both have generous free tiers)

---

### Option B — AWS EC2 (matches your DynamoDB setup)

```bash
# On your EC2 instance (Amazon Linux 2 / Ubuntu)

# Clone repo
git clone <your-repo-url>
cd BotBoundary-main

# Backend
cd Model/login_auth
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend build
cd ../../FrontEnd
npm install && npm run build
# Serve with nginx or any static host
```

---

## API Reference

### `POST /analyze`

**Request:**
```json
{
  "username": "alice",
  "registered_user": false,
  "behavior": {
    "mouse":       { "total_moves": 142, "mean_speed": 3.2, ... },
    "keyboard":    { "total_keystrokes": 18, "mean_interval_ms": 120, ... },
    "interaction": { "click_count": 3, ... },
    "timing":      { "session_duration_ms": 4200, ... },
    "environment": { "viewport_width": 1440, ... }
  }
}
```

**Response:**
```json
{
  "model": "autoencoder",
  "risk_score": 0.0312,
  "threshold": 0.05,
  "is_bot": false,
  "session_id": "uuid-..."
}
```

### `GET /health`
Returns `{"status": "ok"}` — useful for uptime monitoring.

---

## Next Steps for Demo

1. **Collect training data** — run the login page and collect real human sessions, then label them
2. **Train the autoencoder** on human sessions so it has a baseline for "normal"
3. **Create a demo bot script** (Selenium/Playwright with robotic mouse/keyboard timings) to show the model catching it
4. **Build a results dashboard** — query DynamoDB sessions and display risk scores over time
5. **Enable 2FA mode** — after a registered user has 20+ sessions, train their OCSVM and set `registered_user: true`
