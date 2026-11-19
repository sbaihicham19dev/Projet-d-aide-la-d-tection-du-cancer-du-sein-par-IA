"""
Schemas — Detection Service
"""
from pydantic import BaseModel
from typing import Dict, Optional, Any


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    timestamp:    str


class PredictionResponse(BaseModel):
    prediction_id:   str
    filename:        str
    predicted_class: str
    confidence:      float
    probabilities:   Dict[str, float]
    classification:  Optional[Any] = None
    segmentation:    Optional[Any] = None
    birads:          Optional[Any] = None
    localization:    Optional[Any] = None
    tumorsize:       Optional[Any] = None
    visualization:   Optional[Any] = None
    assembler_report: Optional[Any] = None
    stage:           Optional[Any] = None
    narrative:       Optional[Any] = None
    timestamp:       str
