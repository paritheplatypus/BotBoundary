import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from app.models.autoencoder import AutoencoderModel
import os
from preprocess_data import preprocess_csv

import sys
# Allow training script to access app/
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from Model.login_auth.app.core.config import AUTOENCODER_DIR

# Imports for normalization
from sklearn.preprocessing import StandardScaler
import joblib

def train(epochs: int = 40, batch_size: int = 8, learning_rate: float = 0.001):
    """
    Trains autoencoder model on normal data (human)
    X_train: data preprocessed by preprocess_data.py
    """
    feature_df = preprocess_csv("behavioral_events.csv")
    X_train = feature_df.values
    input_dim = X_train.shape[1]

    # Confirm save directory
    os.makedirs(AUTOENCODER_DIR, exist_ok=True)

    # Fit standard scalar for human data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    joblib.dump(scaler, os.path.join(AUTOENCODER_DIR, "scaler.pkl"))

    # Initialize model
    input_dim = X_train.shape[1]
    print("Input dim:", input_dim)
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

    model.train()
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
        print(f"Epoch [{epoch+1}/{epochs}] Loss: {total_loss / len(loader):.6f}")

    # Compute reconstruction errors
    model.eval()
    reconstruction_errors = []

    X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(device)
    with torch.no_grad():
        reconstruction = model(X_tensor)
        errors = torch.mean((reconstruction - X_tensor) ** 2, dim=1)
        reconstruction_errors = errors.cpu().numpy()

    # Reconstruction assessment
    print("Reconstruction Error Stats:")
    errors = errors.cpu().numpy()
    print("Mean:", np.mean(errors))
    print("Std:", np.std(errors))
    print("Min:", np.min(errors))
    print("Max:", np.max(errors))
    print("Percentiles:", np.percentile(errors, [50, 75, 90, 95, 99]))
    
    # Set threshold
    threshold = np.percentile(reconstruction_errors, 95) # 5% of normal sessions will be flagged
    np.save(os.path.join(AUTOENCODER_DIR, "threshold.npy"), threshold)

    # Threshold assessment
    import matplotlib.pyplot as plt
    plt.hist(errors, bins=20)
    plt.axvline(threshold, linestyle='dashed')
    plt.title("Reconstruction Error Distribution")
    plt.xlabel("Error")
    plt.ylabel("Frequency")
    plt.show()

    # Synthetic anomaly test
    noise = np.random.normal(0, 2, X_scaled.shape)
    X_fake = X_scaled + noise
    with torch.no_grad():
        fake_tensor = torch.tensor(X_fake, dtype=torch.float32).to(device)
        fake_recon = model(fake_tensor)
        fake_errors = torch.mean((fake_recon - fake_tensor) ** 2, dim=1).cpu().numpy()

    print("Normal mean error:", np.mean(errors))
    print("Fake anomaly mean error:", np.mean(fake_errors))

    # Save model weights
    torch.save(model.state_dict(), os.path.join(AUTOENCODER_DIR, "autoencoder.pt"))
    print("Training completed. Model, scaler, and threshold saved.")

if __name__ == "__main__":
    train()