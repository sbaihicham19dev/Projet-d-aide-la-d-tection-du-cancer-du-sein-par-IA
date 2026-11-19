"""
Schemas — Stage Service
"""
from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    timestamp:    str


class StageResponse(BaseModel):
    prediction_id: str
    t_stage:       str
    n_stage:       str
    m_stage:       str
    stage:         str        # "IA", "IIB", etc.
    stage_roman:   str        # "I", "II", "III", "IV"
    description:   str
    treatment:     str
    prognosis:     str
    confidence:    float
    timestamp:     str