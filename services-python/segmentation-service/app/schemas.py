"""
Schemas — Segmentation Service
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    timestamp:    str


class SegmentationResponse(BaseModel):
    prediction_id:  str
    filename:       str
    mask_base64:    str        # masque PNG encodé en base64
    tumor_area_px:  int        # nombre de pixels blancs (tumeur)
    tumor_area_pct: float      # pourcentage de l'image
    width:          int        # 224
    height:         int        # 224
    timestamp:      str