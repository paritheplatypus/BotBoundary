"""
schemas.py
CacheMeOutside - Pydantic request / response models for the FastAPI backend.
"""

from pydantic import BaseModel
from typing import Optional


# ── Nested behavior structure matching behaviorTracker.js ──────────────────

class MouseFeatures(BaseModel):
    total_moves: float = 0
    total_distance: float = 0
    normalized_distance: float = 0
    mean_speed: float = 0
    speed_std: float = 0
    max_speed: float = 0
    direction_changes: float = 0
    pause_count: float = 0
    movement_entropy: float = 0


class KeyboardFeatures(BaseModel):
    total_keystrokes: float = 0
    mean_interval_ms: float = 0
    interval_std_ms: float = 0
    min_interval_ms: float = 0
    max_interval_ms: float = 0
    backspace_ratio: float = 0
    paste_detected: bool = False


class InteractionFeatures(BaseModel):
    click_count: float = 0
    scroll_count: float = 0
    focus_changes: float = 0
    mouse_keyboard_ratio: float = 0
    interaction_rate: float = 0


class TimingFeatures(BaseModel):
    session_duration_ms: float = 0
    time_to_first_action_ms: float = 0
    idle_time_ratio: float = 0


class EnvironmentFeatures(BaseModel):
    viewport_width: float = 0
    viewport_height: float = 0
    timezone_offset: float = 0
    device_pixel_ratio: float = 1


class BehaviorPayload(BaseModel):
    mouse: MouseFeatures = MouseFeatures()
    keyboard: KeyboardFeatures = KeyboardFeatures()
    interaction: InteractionFeatures = InteractionFeatures()
    timing: TimingFeatures = TimingFeatures()
    environment: EnvironmentFeatures = EnvironmentFeatures()


# ── Inbound request ────────────────────────────────────────────────────────

class SessionRequest(BaseModel):
    username: str
    password: str
    behavior: BehaviorPayload
    # True  → user has an existing behavioral profile (OCSVM 2FA mode)
    # False → unknown / new user (Autoencoder anomaly detection)


# ── Outbound response ──────────────────────────────────────────────────────

class RiskResponse(BaseModel):
    model: str
    risk_score: float
    threshold: Optional[float] = None
    is_bot: bool
    session_id: Optional[str] = None   # echoed back so the frontend can reference it