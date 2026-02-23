import numpy as np
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

import sys
# Allow training script to access app/
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from app.core.config import USERS_MODEL_DIR

def train(X_train: np.ndarray, user_id: str, nu: float = 0.05, kernerl: str = "rbf", gamma: str = "scale"):
    """
    Trains One-Class SVM for a specific registered user.

    X_train: historical session features vector for one user
    nu: upper bound on fraction of anomalies
    kernel: 'rbf' for non-linear boundary since biometric data is rarely linear
    gamma: kernel coefficient for rbf kernel
    """

    # Models are saved to saved_models/users/user_<id>
    user_dir = os.path.join(USERS_MODEL_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    # Scale the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    joblib.dump(scaler, os.path.join(user_dir, "scaler.pkl"))

    # Train OCSVM
    model = OneClassSVM(nu=nu, kernel=kernerl, gamma=gamma)
    model.fit(X_scaled)
    joblib.dump(model, os.path.join(user_dir, "ocsvm.pkl"))
    print("Training completed.")
