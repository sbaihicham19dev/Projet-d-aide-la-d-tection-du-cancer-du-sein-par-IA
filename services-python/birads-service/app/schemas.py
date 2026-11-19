"""
Schemas — BI-RADS Service
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    timestamp:    str


class BIRADSRequest(BaseModel):
    detection_class:      str
    detection_conf:       float
    classification_class: Optional[str]   = None
    classification_conf:  Optional[float] = None
    tumor_area_pct:       Optional[float] = None


class BIRADSResponse(BaseModel):
    prediction_id:    str
    birads_score:     int            # 0-6
    birads_category:  str            # "4B", "5", etc.
    description:      str
    malignancy_risk:  str
    recommendation:   str
    confidence:       float
    method:           str            # "CNN+ACR" ou "ACR_rules"
    timestamp:        str