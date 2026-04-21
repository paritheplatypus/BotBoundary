import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from app.models.autoencoder import AutoencoderModel
import os
from preprocess_data import preprocess_csv
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

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

def train(epochs: int = 50, batch_size: int = 32, learning_rate: float = 0.001):
    """
    Trains autoencoder model on normal data (human)
    X_train: data preprocessed by preprocess_data.py
    """
    feature_df = preprocess_csv("final_dataset.csv")
    print("\nDATASET DETAILS")
    print(feature_df.shape)
    print(feature_df.columns.tolist())
    print(feature_df.head())

    X= feature_df.values
    input_dim = X.shape[1]

    # Confirm save directory
    os.makedirs(AUTOENCODER_DIR, exist_ok=True)

    # Fit standard scalar for human data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, os.path.join(AUTOENCODER_DIR, "scaler.pkl"))

    # Train/test split
    X_train, X_val = train_test_split(X_scaled, test_size=0.2, random_state=42)
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_tensor = torch.tensor(X_val, dtype=torch.float32)

    # Initialize model
    model_wrapper = AutoencoderModel(input_dim=input_dim)
    model = model_wrapper.model # actual nn.Sequential model
    device = model_wrapper.device
    model.to(device)
    val_tensor = val_tensor.to(device)

    # Define optimizer
    # Adam is adaptive gradient descent which adjusts learning rate per parameter
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Reconstruction loss
    criterion = nn.MSELoss()

    # Prepare dataset
    # Wrap in TensorDataset
    dataset = TensorDataset(torch.tensor(X_scaled, dtype=torch.float32))

    best_val_loss = float("inf")
    patience = 5
    patience_counter = 0
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for batch in train_loader:
            x = batch[0].to(device)

            optimizer.zero_grad()
            reconstruction = model(x)
            loss = criterion(reconstruction, x)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        # --- Validation ---
        model.eval()
        with torch.no_grad():
            val_recon = model(val_tensor)
            val_loss = criterion(val_recon, val_tensor).item()

        print(f"Epoch [{epoch + 1}/{epochs}] "
              f"Train Loss: {avg_train_loss:.6f} | Val Loss: {val_loss:.6f}")

        # --- Early stopping logic ---
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(AUTOENCODER_DIR, "best_autoencoder.pt"))
        else:
            patience_counter += 1

        if patience_counter >= patience:
            print("Early stopping triggered.")
            break

    # --- Load best model ---
    model.load_state_dict(torch.load(os.path.join(AUTOENCODER_DIR, "best_autoencoder.pt")))
    model.eval()

    # --- Compute reconstruction errors on validation set ---
    with torch.no_grad():
        val_recon = model(val_tensor)
        val_errors = torch.mean((val_recon - val_tensor) ** 2, dim=1).cpu().numpy()

    # --- Stats ---
    print("\n--- RECONSTRUCTION ERROR STATS (VALIDATION) ---")
    print("Mean:", np.mean(val_errors))
    print("Std:", np.std(val_errors))
    print("Min:", np.min(val_errors))
    print("Max:", np.max(val_errors))
    print("Percentiles:", np.percentile(val_errors, [50, 75, 90, 95, 97, 99]))

    # --- Threshold (more stable now) ---
    threshold = np.percentile(val_errors, 97)
    np.save(os.path.join(AUTOENCODER_DIR, "threshold.npy"), threshold)

    print(f"\nSelected threshold (97th percentile): {threshold}")

    # --- Plot distribution ---
    plt.hist(val_errors, bins=25)
    plt.axvline(threshold, linestyle='dashed')
    plt.title("Validation Reconstruction Error Distribution")
    plt.xlabel("Error")
    plt.ylabel("Frequency")
    plt.show()

    # --- Synthetic anomaly test ---
    noise = np.random.normal(0, 0.5, X_val.shape)
    X_fake = X_val + noise

    with torch.no_grad():
        fake_tensor = torch.tensor(X_fake, dtype=torch.float32).to(device)
        fake_recon = model(fake_tensor)
        fake_errors = torch.mean((fake_recon - fake_tensor) ** 2, dim=1).cpu().numpy()

    print("\n--- ANOMALY TEST ---")
    print("Normal mean error:", np.mean(val_errors))
    print("Fake anomaly mean error:", np.mean(fake_errors))

    # --- Save final model ---
    torch.save(model.state_dict(), os.path.join(AUTOENCODER_DIR, "autoencoder.pt"))

    print("\nTraining completed. Model, scaler, and threshold saved.")

if __name__ == "__main__":
    train()