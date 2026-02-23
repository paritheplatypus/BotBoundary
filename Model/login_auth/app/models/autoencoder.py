from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn as nn
import joblib

from app.models.base_model import Basemodel
from app.core.config import AUTOENCODER_DIR


class AutoencoderModel(Basemodel):
    """
    Wrapper for the autoencoder model
     This class object does two things:
       1. Defines the neural network architecture
       2. Provides an inference interface for our API structure
    Training is done separately in /training/train_autoencoder.py
    This class only loads the trained weights and runs inference
    """

    def __init__(self, input_dim: int, latent_dim: int = 16):
        self.model_name = "autoencoder"
        self.input_dim = input_dim # number of features in session vector
        self.latent_dim = latent_dim # size of compressed representation (bottleneck layer)
        self.model_path = AUTOENCODER_DIR # path to saved model weights (.pt file)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # use gpu is avaliable

        """
        Architechture defined
        
        nn.Sequential allows stacking layers, each layer transforms the last layers output
        Encoder: compress input -> Latent space
        Decoder: reconstruct Latent -> original dimension
        
        Structure:
        Input -> 128 -> 64 -> Latent -> 64 -> 128 -> Output
        """
        self.model = nn.Sequential(
            # First encoder layer
            nn.Linear(input_dim, 128), # fully connected layer
            nn.ReLU(), # non-linear activation

            # Second encoder layer
            nn.Linear(128, 64),
            nn.ReLU(),

            # Bottleneck layer, contains signifigantly fewer  neurons to force compression
            nn.Linear(64, latent_dim),
            nn.ReLU(),

            # Decoder begins
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),

            # Final reconstruction layer
            nn.Linear(128, input_dim)
        ).to(self.device) # mode model to CPU or GPU

        # MSE Loss to measure reconstruction error
        # Formula: mean((x - x_hat)^2)
        self.criterion = nn.MSELoss()

        self.scaler = None
        self.threshold = None
        self._fallback = False

    def load(self):
        """
        Load trained model weights, scaler, and threshold from disk
        This doesn't re-train the model
        """
        weights_path = os.path.join(self.model_path, "autoencoder.pt")
        scaler_path = os.path.join(self.model_path, "scaler.pkl")
        threshold_path = os.path.join(self.model_path, "threshold.npy")

        # If artifacts are missing (common early in the project), fall back to a simple heuristic.
        if not (os.path.exists(weights_path) and os.path.exists(scaler_path) and os.path.exists(threshold_path)):
            self._fallback = True
            self.threshold = 1.0
            return

        self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.scaler = joblib.load(scaler_path)
        thr = np.load(threshold_path)
        self.threshold = float(thr.item() if hasattr(thr, "item") else thr)
        self.model.eval()


    def predict(self, feature_vector):

        """
        Runs a forward pass and computes reconstruction error
        feature_vector: list of floats
        Returns:
        {
            "model_name": str,
            "score": float (reconstruction error)
        }
        """

        if self._fallback:
            # Lightweight heuristic (keeps the pipeline functional until training artifacts exist).
            # Feature order matches Backend/api/app/services/feature_vector.py.
            # Heuristic focuses on "too fast / too empty" sessions.
            try:
                total_keystrokes = float(feature_vector[9])
                click_count = float(feature_vector[16])
                session_duration_ms = float(feature_vector[21])
                time_to_first_action_ms = float(feature_vector[22])
                paste_detected = float(feature_vector[15])
            except Exception:
                total_keystrokes, click_count, session_duration_ms, time_to_first_action_ms, paste_detected = 0, 0, 0, 0, 0

            risk = 0.0
            if session_duration_ms < 600:
                risk += 0.5
            if time_to_first_action_ms < 80:
                risk += 0.25
            if total_keystrokes == 0 and click_count == 0:
                risk += 0.25
            if paste_detected > 0:
                risk += 0.25
            risk = min(1.0, risk)
            is_anomaly = risk >= 0.95
            return {
                "model_name": self.model_name,
                "score": float(risk),
                "threshold": 1.0,
                "is_anomaly": bool(is_anomaly),
            }

        # Scale features
        scaled = self.scaler.transform([feature_vector])[0]

        # Convert to tensor with batch dim
        x = torch.tensor(scaled, dtype=torch.float32, device=self.device).unsqueeze(0)

        # Disable gradient tracking during inference to save memory, speed up computation, and prevent accidental training
        with torch.no_grad():
            # Forward pass
            reconstruction = self.model(x)
            error = self.criterion(reconstruction, x)
        error_value = float(error.item())

        threshold = float(self.threshold or 1.0)
        is_anomaly = error_value > threshold

        return {
            "model_name": self.model_name,
            "score": error_value,
            "threshold": float(threshold),
            "is_anomaly": bool(is_anomaly)
        }