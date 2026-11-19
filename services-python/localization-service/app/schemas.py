"""
Schemas — Localization Service
"""
from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    timestamp:    str


class LocalizationResponse(BaseModel):
    prediction_id:   str
    filename:        str
    quadrant:        str        # "UO", "UI", "LO", "LI", "C", "N"
    quadrant_name:   str        # "Upper Outer (Haut Externe)"
    quadrant_fr:     str        # "Quadrant supéro-externe"
    centroid_x:      float      # position X normalisée (0-1)
    centroid_y:      float      # position Y normalisée (0-1)
    centroid_x_px:   int        # position X en pixels
    centroid_y_px:   int        # position Y en pixels
    tumor_area_pct:  float      # % surface tumorale
    confidence:      float
    timestamp:       str