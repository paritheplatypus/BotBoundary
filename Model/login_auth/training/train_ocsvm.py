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
from preprocess_data import preprocess_csv
from app.services.feature_extractor import FEATURE_ORDER

def train(file_path: str, user_id: str, nu: float = 0.05, kernel: str = "rbf", gamma: str = "scale"):
    """
    Trains One-Class SVM for a specific registered user.

    X_train: historical session features vector for one user
    nu: upper bound on fraction of anomalies
    kernel: 'rbf' for non-linear boundary since biometric data is rarely linear
    gamma: kernel coefficient for rbf kernel
    """

    # Models are saved to saved_models/users/user_<id>
    feature_df = preprocess_csv(file_path)
    print("\nDATASET DETAILS")
    print(feature_df.shape)
    print(feature_df.head())

    if feature_df.empty:
        raise ValueError("No valid data after preprocessing.")

    X = feature_df.values

    # Save to directory
    user_dir = os.path.join(USERS_MODEL_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    # Scale data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    gamma = 1 / X_scaled.shape[1]

    joblib.dump(scaler, os.path.join(user_dir, "scaler.pkl"))

    # Save feature order
    joblib.dump(FEATURE_ORDER, os.path.join(user_dir, "feature_order.pkl"))

    # Train OCSVM
    model = OneClassSVM(
        nu=nu,
        kernel=kernel,
        gamma=gamma
    )

    model.fit(X_scaled)

    joblib.dump(model, os.path.join(user_dir, "ocsvm.pkl"))

    print("\nTraining completed.")
    print(f"Model saved to: {user_dir}")


if __name__ == "__main__":
    train(
        file_path="2fa_data.csv",
        user_id="nolanpark"
    )