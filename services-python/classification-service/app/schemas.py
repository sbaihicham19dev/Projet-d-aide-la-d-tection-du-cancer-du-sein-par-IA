"""
Schemas — Classification Service
"""
from pydantic import BaseModel
from typing import Dict
from datetime import datetime


class ClassificationResponse(BaseModel):
    prediction_id: str
    filename: str
    predicted_class: str        # "Benign" ou "Malignant"
    confidence: float
    probabilities: Dict[str, float]
    timestamp: datetime