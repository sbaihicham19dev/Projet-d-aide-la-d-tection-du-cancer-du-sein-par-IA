from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str


class VisualizationResponse(BaseModel):
    prediction_id: str
    filename: str
    method: str
    quality_warning: Optional[str] = None
    overlay_base64: Optional[str] = None
    heatmap_base64: Optional[str] = None
    lesion_base64: Optional[str] = None
    lesion_bbox: Optional[list[int]] = None
    focus_score: float = Field(ge=0.0, le=1.0)
    tumor_area_pct: Optional[float] = None
    width: int
    height: int
    timestamp: str
