import os

# Absolute path to root, necessary for EC2 server system
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Model directories
AUTOENCODER_DIR = os.path.join(BASE_DIR, 'saved_models', 'autoencoder')
USERS_MODEL_DIR = os.path.join(BASE_DIR, 'saved_models', 'user')

# Enviornment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

