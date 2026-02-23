from __future__ import annotations

import math


class ScoreService:
    """Normalizes model outputs into a consistent 0..1 risk score.

    - Autoencoder: risk ≈ error / threshold (capped at 1)
    - One-Class SVM: risk ≈ sigmoid(-distance) (more negative => higher risk)
    """

    def process(self, model_output: dict):
        name = model_output.get("model_name", "unknown")

        if name == "autoencoder":
            error = float(model_output.get("score", 0.0))
            threshold = float(model_output.get("threshold", 1.0)) or 1.0
            risk = min(1.0, max(0.0, error / threshold))
            return {
                "model_used": name,
                "risk_score": float(risk),
                "threshold": float(threshold),
                "is_anomaly": bool(model_output.get("is_anomaly", False)),
                "raw_score": float(error),
            }

        # one_class_svm (or any distance-based model)
        dist = float(model_output.get("score", 0.0))
        # sigmoid(-dist) => dist<0 increases risk
        risk = 1.0 / (1.0 + math.exp(dist))
        return {
            "model_used": name,
            "risk_score": float(risk),
            "threshold": 0.0,
            "is_anomaly": bool(model_output.get("is_anomaly", False)),
            "raw_score": float(dist),
        }