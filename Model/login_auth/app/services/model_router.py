from app.models.autoencoder import AutoencoderModel
from app.models.ocsvm import OneClassSVMModel

class ModelRouter():
    def __init__(self, autoencoder, ocsvm):
        self.autoencoder = autoencoder
        self.ocsvm = ocsvm

    def route(self, registered_user: bool, user_id: str = None):
        if registered_user:
            if user_id is None:
                raise Exception("User id is required")
            model = OneClassSVMModel(user_id=user_id)
        else:
            model = AutoencoderModel()

        model.load()
        return model