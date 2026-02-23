from app.models.base_model import Basemodel
import os
import joblib
from app.core.config import USERS_MODEL_DIR

class OneClassSVMModel(Basemodel):

    """
    Wrapper class for One-Class SVM inference

    Used for registered users as a form of 2fa with biometric data
    """
    def __init__(self, user_id: str):
        self.model_name = "one_class_svm"
        self.user_id = user_id
        self.model_dir = os.path.join(USERS_MODEL_DIR, f"user_{user_id}")
        self.model = None
        self.scaler = None

    def load(self):
        # Confirms the user has an existing directory
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(f"Model directory {self.model_dir} does not exist")

        # Load trained SVM and scaler
        self.model = joblib.load(os.path.join(self.model_dir, "ocsvm.pkl"))
        self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.pkl"))


    def predict(self, feature_vector: list):
        """
        returns:
            score = signed distance from decision boundary
            is_anomaly = true if outside the decision boundary
        """

        # Scale input
        scaled = self.scaler.transform([feature_vector])

        # Decision function
        score = self.model.decision_function(scaled)[0] # decision given distance from the boundary

        # Predict returns +1 for an inlier and -1 for an anomaly
        prediction = self.model.predict(scaled)[0]
        is_anomaly = prediction == -1

        return {
            "model_name": self.model_name,
            "score": float(score),
            "is_anomaly": bool(is_anomaly)
        }