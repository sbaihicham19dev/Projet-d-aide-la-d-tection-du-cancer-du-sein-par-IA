from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    llm_enabled: bool
    timestamp: str


class NarrativeRequest(BaseModel):
    report: Dict[str, Any]
    language: str = "fr"
    include_disclaimer: bool = True


class NarrativeResponse(BaseModel):
    prediction_id: str
    filename: str
    language: str
    title: str
    impression: str
    findings: List[str]
    stage_summary: str
    recommendations: List[str]
    limitations: List[str]
    narrative_text: str
    model: str
    timestamp: datetime
