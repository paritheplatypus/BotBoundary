class ScoreService:
    """Formats raw model output into the API response shape."""

    def process(self, model_output: dict) -> dict:
        return {
            "model":       model_output["model_name"],
            "risk_score":  model_output["score"],
            "threshold":   model_output.get("threshold"),   # None for OCSVM
            "is_bot":      model_output["is_anomaly"],
        }