from pydantic import BaseModel
from typing import Optional

class PredictionResponse(BaseModel):
    label: str
    confidence: float
    probabilities: dict

class HealthResponse(BaseModel):
    status: str
    model: str
    version: str