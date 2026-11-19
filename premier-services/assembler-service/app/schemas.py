from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str


class PipelineInputs(BaseModel):
    prediction_id: Optional[str] = None
    filename: Optional[str] = None
    detection: Optional[Dict[str, Any]] = None
    classification: Optional[Dict[str, Any]] = None
    segmentation: Optional[Dict[str, Any]] = None
    birads: Optional[Dict[str, Any]] = None
    localization: Optional[Dict[str, Any]] = None
    tumorsize: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    n_stage: str = "N0"
    m_stage: str = "M0"


class StageResponse(BaseModel):
    t_stage: str
    n_stage: str
    m_stage: str
    stage: str
    stage_roman: str
    description: str
    treatment: str
    prognosis: str
    confidence: float


class AssembledReport(BaseModel):
    prediction_id: str
    filename: str
    status: str
    completeness: float = Field(ge=0.0, le=1.0)
    missing_results: List[str]
    risk_level: str
    clinical_summary: str
    recommendations: List[str]
    quality_warnings: List[str]
    detection: Optional[Dict[str, Any]] = None
    classification: Optional[Dict[str, Any]] = None
    segmentation: Optional[Dict[str, Any]] = None
    birads: Optional[Dict[str, Any]] = None
    localization: Optional[Dict[str, Any]] = None
    tumorsize: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    stage: StageResponse
    timestamp: datetime
