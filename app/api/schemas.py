from pydantic import BaseModel
from typing import Literal

class RedFlag(BaseModel):
    flag: str
    evidence: str

class PredictResponse(BaseModel):
    risk_score: float
    verdict: Literal["low_risk", "medium_risk", "high_risk"]
    red_flags: list[RedFlag]
    confidence: float

class PredictRequest(BaseModel):
    posting_text: str