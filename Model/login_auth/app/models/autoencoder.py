from app.models.base_model import Basemodel
import torch
import torch.nn as nn
import numpy as np
from app.core.config import AUTOENCODER_DIR

# import for normalization scaler
import joblib
import os


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

    def load(self):
        """
        Load trained model weights, scaler, and threshold from disk
        This doesn't re-train the model
        """
        self.model.load_state_dict(torch.load(os.path.join(self.model_path, "autoencoder.pt"), map_location=self.device))

        self.scaler = joblib.load(os.path.join(self.model_path, "scaler.pkl"))
        self.threshold = np.load(os.path.join(self.model_path, "threshold.npy"))
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

        # Scale features
        scaled = self.scaler.transform([feature_vector])

        # Convert list to Pytorch tensor
        # Use standard dtype = float32 for neural networks
        x = torch.tensor(feature_vector, dtype=torch.float32).to(self.device)

        # Disable gradient tracking during inference to save memory, speed up computation, and prevent accidental training
        with torch.no_grad():
            # Forward pass
            reconstruction = self.model(x)

            # Compute reconstruction error
            error = self.criterion(reconstruction, x)
        error_value = error.item()

        # Compare error with threshold
        is_anomaly = error_value > self.threshold

        return {
            "model_name": self.model_name,
            "score": error_value,
            "threshold": float(self.threshold),
            "is_anomaly": bool(is_anomaly)
        }