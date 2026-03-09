from app.models.autoencoder import AutoencoderModel
from app.models.ocsvm import OneClassSVMModel
from app.services.feature_extractor import FEATURE_DIM


class ModelRouter:
    """
    Routes a session to the correct ML model:
      - Unregistered / new user  → Autoencoder  (general bot detection)
      - Registered user          → OneClassSVM  (per-user 2FA / owner check)
    """

    def __init__(self, autoencoder: AutoencoderModel, ocsvm_cache: dict):
        # Pre-loaded global autoencoder instance
        self.autoencoder = autoencoder
        # Cache of per-user OCSVM models so we don't reload on every request
        self._ocsvm_cache: dict = ocsvm_cache

    def route(self, registered_user: bool, user_id: str | None = None):
        if registered_user:
            if user_id is None:
                raise ValueError("user_id is required when registered_user=True")

            if user_id not in self._ocsvm_cache:
                model = OneClassSVMModel(user_id=user_id)
                model.load()
                self._ocsvm_cache[user_id] = model

            return self._ocsvm_cache[user_id]

        # Default: general anomaly detection via Autoencoder
        return self.autoencoder