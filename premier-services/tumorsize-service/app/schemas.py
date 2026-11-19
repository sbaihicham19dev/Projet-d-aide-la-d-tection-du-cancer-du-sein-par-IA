"""
Schemas — TumorSize Service
"""
from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    timestamp:    str


class TumorSizeResponse(BaseModel):
    prediction_id:    str
    filename:         str

    # Pixels
    width_px:         int
    height_px:        int
    area_px:          int
    area_pct:         float

    # Centimètres
    width_cm:         float
    height_cm:        float
    diameter_cm:      float
    area_cm2:         float

    # Classification TNM
    tnm_stage:        str     # "T1a", "T1b", "T1c", "T2", "T3"
    tnm_desc:         str

    # Paramètres
    pixel_spacing_mm: float
    original_size_px: int

    timestamp:        str