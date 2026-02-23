from fastapi import FastAPI
from app.schemas import SessionRequest, RiskResponse
from app.services.model_router import ModelRouter
from app.services.score_service import ScoreService
from app.models.autoencoder import AutoencoderModel
from app.models.ocsvm import OneClassSVMModel

app = FastAPI(title = "Login CAPTCHA")

# load models at startup so they're only loaded once
autoencoder = AutoencoderModel()
ocsvm = OneClassSVMModel()
autoencoder.load()
ocsvm.load()
router = ModelRouter(autoencoder, ocsvm)
score_service = ScoreService()

# app.post makes it so if someone sends a post request to /analyze run this function with a recieved JSON
@app.post("/analyze", response_model=RiskResponse)
def analyze_session(request: SessionRequest): # FastAPI converts JSON into python data
    # selects the appropriate model
    model = router.route(request.registered_user) #function call to model_router's route function

    # recieves score
    model_output = model.predict(request.features) #runs either models predict function

    # process risk score
    final = score_service.process(model_output) #final risk score gets sent to score_service to be processed

    return final
