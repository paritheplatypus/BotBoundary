from app.models.base_model import Basemodel
import os
import joblib
from app.core.config import USERS_MODEL_DIR
from app.services.feature_extractor import FEATURE_ORDER

class OneClassSVMModel(Basemodel):

    """
    Wrapper class for One-Class SVM inference

    Used for registered users as a form of 2fa with biometric data
    """
    def __init__(self, user_id: str = "nolanpark"):
        self.model_name = "one_class_svm"
        self.user_id = user_id

        # IMPORTANT: per-user model directory
        self.model_dir = os.path.join(USERS_MODEL_DIR, f"user_{user_id}")

        self.model = None
        self.scaler = None

        # Match training schema
        self.feature_columns = FEATURE_ORDER

    def load(self):
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(
                f"Model directory {self.model_dir} does not exist"
            )

        self.model = joblib.load(os.path.join(self.model_dir, "ocsvm.pkl"))
        self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.pkl"))


    def predict(self, parsed_features: dict):
        """
        parsed_features: flattened dict from main.py

        returns:
            score = signed distance from decision boundary
            is_anomaly = true if outside the boundary
        """

        # Align features exactly like training
        feature_vector = [
            float(
                parsed_features.get(col, 0.0)
                or parsed_features.get(col.split(".")[-1], 0.0)
            )
            for col in self.feature_columns
        ]

        # Scale input
        scaled = self.scaler.transform([feature_vector])

        # Decision function (distance from boundary)
        score = self.model.decision_function(scaled)[0]

        # Prediction: +1 (inlier), -1 (anomaly)
        prediction = self.model.predict(scaled)[0]
        is_anomaly = prediction == -1

        return {
            "model_name": self.model_name,
            "score": float(score),
            "threshold": 0.0,  # optional, OCSVM doesn't use explicit threshold
            "is_anomaly": bool(is_anomaly),
        }