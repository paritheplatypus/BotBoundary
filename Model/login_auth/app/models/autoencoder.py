from Model.login_auth.app.models.base_model import Basemodel
import torch
import torch.nn as nn
import numpy as np
from app.core.config import AUTOENCODER_DIR
from app.services.feature_extractor import FEATURE_DIM
from app.services.feature_extractor import FEATURE_ORDER
from app.services.feature_extractor import flatten_behavior

import joblib
import os


class AutoencoderModel(Basemodel):
    """
    Wrapper for the autoencoder model.
    Defines the neural network architecture and provides an inference interface.
    Training is done separately in /training/train_autoencoder.py.
    This class only loads trained weights and runs inference.
    """

    def __init__(self, input_dim: int = FEATURE_DIM, latent_dim: int = 16):
        self.model_name = "autoencoder"
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.model_path = AUTOENCODER_DIR
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_columns = FEATURE_ORDER

        """
        Architecture:
        Input -> 128 -> 64 -> Latent -> 64 -> 128 -> Output
        """
        self.model = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim),
            nn.ReLU(),
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim)
        ).to(self.device)

        self.criterion = nn.MSELoss()
        self.scaler = None
        self.threshold = None

    def load(self):
        """
        Load trained model weights, scaler, and threshold from disk
        This doesn't re-train the model
        """
        self.model.load_state_dict(torch.load(os.path.join(self.model_path, "best_autoencoder.pt"), map_location=self.device))

        self.scaler = joblib.load(os.path.join(self.model_path, "scaler.pkl"))
        self.threshold = np.load(os.path.join(self.model_path, "threshold.npy"))
        self.model.eval()


    def predict(self, parsed_features: dict):

        """
        Runs a forward pass and computes reconstruction error
        feature_vector: list of floats
        Returns:
        {
            "model_name": str,
            "score": float (reconstruction error)
        }
        """

        # Align prediction feature order with training order
        feature_vector = [
            float(
                parsed_features.get(col, 0.0)
                or parsed_features.get(col.split(".")[-1], 0.0)
            )
            for col in self.feature_columns
        ]

        # Scale features
        scaled = self.scaler.transform([feature_vector])
        # print("SCALED INPUT:", scaled)

        # Convert list to Pytorch tensor
        # Use standard dtype = float32 for neural networks
        x = torch.tensor(scaled, dtype=torch.float32).to(self.device)

        # Disable gradient tracking during inference to save memory, speed up computation, and prevent accidental training
        with torch.no_grad():
            # Forward pass
            reconstruction = self.model(x)

            # Compute reconstruction error
            error = self.criterion(reconstruction, x)
        error_value = error.item()

        # Compare error with threshold
        is_anomaly = error_value > self.threshold

        # print("RAW FEATURE VECTOR:", feature_vector[:10])
        # print("NON-ZERO COUNT:", sum(v != 0 for v in feature_vector))

        return {
            "model_name": self.model_name,
            "score": error_value,
            "threshold": float(self.threshold),
            "is_anomaly": bool(is_anomaly)
        }
