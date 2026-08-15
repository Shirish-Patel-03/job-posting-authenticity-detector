# app/api/main.py — the real route, stays unchanged when you swap the model later
from fastapi import FastAPI
from app.api.schemas import PredictRequest, PredictResponse
from app.api.mock_model import mock_predict

app = FastAPI()

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    return mock_predict(request.posting_text)