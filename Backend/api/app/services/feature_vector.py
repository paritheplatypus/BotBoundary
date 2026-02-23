from __future__ import annotations

from typing import Any, Dict, List


# The project documentation describes converting behavioral events into a fixed-dimensional feature vector
# for inference. This function deterministically maps the FrontEnd/src/behavior/behaviorTracker.js output
# into a List[float] in a consistent order.


FEATURE_ORDER: List[str] = [
    # mouse
    "mouse.total_moves",
    "mouse.total_distance",
    "mouse.normalized_distance",
    "mouse.mean_speed",
    "mouse.speed_std",
    "mouse.max_speed",
    "mouse.direction_changes",
    "mouse.pause_count",
    "mouse.movement_entropy",
    # keyboard
    "keyboard.total_keystrokes",
    "keyboard.mean_interval_ms",
    "keyboard.interval_std_ms",
    "keyboard.min_interval_ms",
    "keyboard.max_interval_ms",
    "keyboard.backspace_ratio",
    "keyboard.paste_detected",
    # interaction
    "interaction.click_count",
    "interaction.scroll_count",
    "interaction.focus_changes",
    "interaction.mouse_keyboard_ratio",
    "interaction.interaction_rate",
    # timing
    "timing.session_duration_ms",
    "timing.time_to_first_action_ms",
    "timing.idle_time_ratio",
    # environment
    "environment.viewport_width",
    "environment.viewport_height",
    "environment.timezone_offset",
    "environment.device_pixel_ratio",
]


def _get(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return 0
        cur = cur.get(part)
        if cur is None:
            return 0
    return cur


def behavior_to_feature_vector(behavior: Dict[str, Any]) -> List[float]:
    vec: List[float] = []
    for key in FEATURE_ORDER:
        val = _get(behavior, key)
        if isinstance(val, bool):
            vec.append(1.0 if val else 0.0)
        else:
            try:
                vec.append(float(val))
            except (TypeError, ValueError):
                vec.append(0.0)
    return vec
