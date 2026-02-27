from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import SessionRequest, RiskResponse, LoginRequest, LoginResponse

from app.database import (
    get_user_by_username,
    create_session,
    update_session_result,
    log_behavioral_event
)

app = FastAPI(title="BotBoundary - Login CAPTCHA")

# Allow the frontend (running in the browser) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace * with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "BotBoundary API is running"}


@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Main login endpoint. Called by the frontend on form submit.

    1. Looks up the user in DynamoDB
    2. Creates a session
    3. Logs the raw behavioral data to DynamoDB
    4. Flattens behavioral data into a feature vector
    5. Runs it through the ML model (placeholder until torch is installed)
    6. Saves the ML result back to DynamoDB
    7. Returns verdict to the frontend
    """

    # 1. Look up user
    user = get_user_by_username(request.username)
    registered_user = user is not None
    user_id = user["userId"] if user else "anonymous"

    # 2. Create a session in DynamoDB
    session = create_session(user_id)
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")
    session_id = session["sessionId"]

    # 3. Log raw behavioral data to DynamoDB
    b = request.behavior
    log_behavioral_event(session_id, "mouse",       b.get("mouse", {}))
    log_behavioral_event(session_id, "keyboard",    b.get("keyboard", {}))
    log_behavioral_event(session_id, "interaction", b.get("interaction", {}))
    log_behavioral_event(session_id, "timing",      b.get("timing", {}))
    log_behavioral_event(session_id, "environment", b.get("environment", {}))

    # 4. Flatten behavioral data into a feature vector
    feature_vector = flatten_behavior(b)
    print(f"[API] Feature vector ({len(feature_vector)} features): {feature_vector}")

    # 5. ML model placeholder — swap this out once torch is installed
    # When the model team is ready, re-add the model imports at the top
    # and replace this block with the real model call
    final = {
        "risk_score": 0.0,
        "is_bot": False,
        "model_used": "placeholder"
    }

    # 6. Save the ML result back to DynamoDB
    update_session_result(
        session_id=session_id,
        user_id=user_id,
        ml_score=final["risk_score"],
        is_bot=final["is_bot"]
    )

    # 7. Return verdict to frontend
    return LoginResponse(
        session_id=session_id,
        is_bot=final["is_bot"],
        risk_score=final["risk_score"],
        model_used=final["model_used"],
        registered_user=registered_user
    )


def flatten_behavior(behavior: dict) -> list:
    """
    Converts the nested behavior dict from the frontend into a flat
    list of 20 floats that the ML model consumes.

    The order here must stay consistent — the model was trained on
    features in this exact order.
    """
    mouse       = behavior.get("mouse", {})
    keyboard    = behavior.get("keyboard", {})
    interaction = behavior.get("interaction", {})
    timing      = behavior.get("timing", {})

    return [
        # Mouse (9 features)
        float(mouse.get("total_moves", 0)),
        float(mouse.get("total_distance", 0)),
        float(mouse.get("normalized_distance", 0)),
        float(mouse.get("mean_speed", 0)),
        float(mouse.get("speed_std", 0)),
        float(mouse.get("max_speed", 0)),
        float(mouse.get("direction_changes", 0)),
        float(mouse.get("pause_count", 0)),
        float(mouse.get("movement_entropy", 0)),

        # Keyboard (6 features)
        float(keyboard.get("total_keystrokes", 0)),
        float(keyboard.get("mean_interval_ms", 0)),
        float(keyboard.get("interval_std_ms", 0)),
        float(keyboard.get("min_interval_ms", 0)),
        float(keyboard.get("max_interval_ms", 0)),
        float(keyboard.get("backspace_ratio", 0)),

        # Interaction (3 features)
        float(interaction.get("click_count", 0)),
        float(interaction.get("scroll_count", 0)),
        float(interaction.get("mouse_keyboard_ratio", 0)),

        # Timing (2 features)
        float(timing.get("session_duration_ms", 0)),
        float(timing.get("idle_time_ratio", 0)),
    ]
    # Total: 20 features — matches AutoencoderModel(input_dim=20)
