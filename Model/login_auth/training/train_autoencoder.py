import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from app.models.autoencoder import AutoencoderModel
import os

import sys
# Allow training script to access app/
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from app.core.config import AUTOENCODER_DIR

# Imports for normalization
from sklearn.preprocessing import StandardScaler
import joblib

def train(X_train: np.ndarray, y_train: np.ndarray, input_dim: int, epochs: int = 50, batch_size: int = 64, learning_rate: float = 0.0001):
    """
    Trains autoencoder model on normal data (human)
    X_train: numpy array of shape (num_samples, input_dim)
    """

    # Confirm save directory
    os.makedirs(AUTOENCODER_DIR, exist_ok=True)

    # Fit standard scalar for human data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    joblib.dump(scaler, os.path.join(AUTOENCODER_DIR, "scaler.pkl"))

    # Initialize model
    model_wrapper = AutoencoderModel(input_dim=input_dim)
    model = model_wrapper.model # actual nn.Sequential model
    device = model_wrapper.device

    # Define optimizer
    # Adam is adaptive gradient descent which adjusts learning rate per parameter
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Reconstruction loss
    criterion = nn.MSELoss()

    # Prepare dataset
    # Wrap in TensorDataset
    dataset = TensorDataset(torch.tensor(X_scaled, dtype=torch.float32))

    # Dataloader handles batching and shuffling
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Training loop
    for epoch in range(epochs):
        total_loss = 0

        # Loop over batches
        for batch in loader:
            # Extract features
            x = batch[0].to(device)

            # Clear previous gradients which accumulate by default in pytorch
            optimizer.zero_grad()

            # Forward pass
            reconstruction = model(x)

            # Compute loss
            loss = criterion(reconstruction, x)

            # Backpropagation computing the derivative loss/parameters
            loss.backward()

            # Update parameters
            optimizer.step()

            total_loss += loss.item()
        print(f"Epoch [{epoch+1}/{epochs}] Loss: {total_loss:.6f}")

    # Compute reconstruction errors
    model.eval()
    reconstruction_errors = []

    with torch.no_grad():
        for x in torch.tensor(X_scaled, dtype=torch.float32).to(device):
            x = x.unsqueeze(0)
            reconstruction = model(x)
            error = torch.mean((reconstruction - x) ** 2)
            reconstruction_errors.append(error.item())
    reconstruction_errors = np.array(reconstruction_errors)
    
    # Set threshold
    threshold = np.percentile(reconstruction_errors, 95) # 5% of normal sessions will be flagged
    np.save(os.path.join(AUTOENCODER_DIR, "threshold.npy"), threshold)

    # Save model weights
    torch.save(model.state_dict(), os.path.join(AUTOENCODER_DIR, "autoencoder.pt"))
    print("Training completed. Model, scaler, and threshold saved.")

