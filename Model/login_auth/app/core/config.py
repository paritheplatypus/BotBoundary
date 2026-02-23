import os

# Root of the model service (Model/login_auth)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Model directories (stored alongside the service code)
AUTOENCODER_DIR = os.path.join(BASE_DIR, 'saved_models', 'autoencoder')
USERS_MODEL_DIR = os.path.join(BASE_DIR, 'saved_models', 'user')

# Enviornment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

