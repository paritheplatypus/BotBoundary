"""
feature_extractor.py
CacheMeOutside

Converts the nested behavior object sent from the frontend into a flat
feature vector that the ML models expect.

Frontend sends:
{
  mouse:       { total_moves, total_distance, normalized_distance, mean_speed,
                 speed_std, max_speed, direction_changes, pause_count, movement_entropy },
  keyboard:    { total_keystrokes, mean_interval_ms, interval_std_ms, min_interval_ms,
                 max_interval_ms, backspace_ratio, paste_detected },
  interaction: { click_count, scroll_count, focus_changes,
                 mouse_keyboard_ratio, interaction_rate },
  timing:      { session_duration_ms, time_to_first_action_ms, idle_time_ratio },
  environment: { viewport_width, viewport_height, timezone_offset, device_pixel_ratio }
}

Models expect: List[float] of length FEATURE_DIM (24)
"""

from typing import List

# The canonical feature order. Must stay in sync with training scripts.
FEATURE_ORDER = [
    # Mouse (9)
    "mouse.total_moves",
    "mouse.total_distance",
    "mouse.normalized_distance",
    "mouse.mean_speed",
    "mouse.speed_std",
    "mouse.max_speed",
    "mouse.direction_changes",
    "mouse.pause_count",
    "mouse.movement_entropy",
    # Keyboard (7)
    "keyboard.total_keystrokes",
    "keyboard.mean_interval_ms",
    "keyboard.interval_std_ms",
    "keyboard.min_interval_ms",
    "keyboard.max_interval_ms",
    "keyboard.backspace_ratio",
    "keyboard.paste_detected",        # bool -> 0.0 / 1.0
    # Interaction (5)
    "interaction.click_count",
    "interaction.scroll_count",
    "interaction.focus_changes",
    "interaction.mouse_keyboard_ratio",
    "interaction.interaction_rate",
    # Timing (3)
    "timing.session_duration_ms",
    "timing.time_to_first_action_ms",
    "timing.idle_time_ratio",
]

FEATURE_DIM = len(FEATURE_ORDER)  # 24


def flatten_behavior(behavior: dict) -> List[float]:
    """
    Flatten the nested behavior dict from the frontend into an ordered
    flat list of floats ready for model inference.

    Args:
        behavior: Nested dict as sent by behaviorTracker.js

    Returns:
        List of FEATURE_DIM floats in canonical order.

    Raises:
        ValueError if a required feature is missing.
    """
    vector = []

    for key in FEATURE_ORDER:
        group, field = key.split(".", 1)

        group_data = behavior.get(group, {})
        raw = group_data.get(field)

        if raw is None:
            # Missing feature — default to 0.0 so a bad frontend payload
            # doesn't crash inference. Log it so the team can catch drift.
            print(f"[WARN] feature_extractor: missing feature '{key}', defaulting to 0.0")
            raw = 0.0

        # Convert booleans to float
        if isinstance(raw, bool):
            raw = 1.0 if raw else 0.0

        vector.append(float(raw))

    return vector
