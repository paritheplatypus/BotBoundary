class ScoreService:

    # Handles the final formatting and business logic
    def process(self, model_output: dict):
        return {
            "model_used": model_output["model_name"],
            "risk_score": model_output["score"],
            "threshold": model_output["threshold"],
            "is_bot": model_output["is_anomaly"]
        }