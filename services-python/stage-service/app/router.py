"""
Router — Stage Service
POST /api/v1/stage → stade TNM I-IV
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request
from app.schemas import StageResponse, HealthResponse
from app.staging import stage_from_pipeline

logger = logging.getLogger("stage.router")
router = APIRouter(prefix="/api/v1", tags=["Staging"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    return HealthResponse(status="ok", model_loaded=True,
                          timestamp=datetime.utcnow().isoformat())


@router.post(
    "/stage",
    response_model=StageResponse,
    summary="Staging TNM",
    description=(
        "Détermine le stade du cancer (I→IV) selon AJCC 8e édition.\n\n"
        "Paramètres :\n"
        "- diameter_cm          : diamètre tumeur en cm (depuis tumorsize-service)\n"
        "- tnm_stage            : stade T direct (T1a, T1c, T2...) optionnel\n"
        "- classification_class : Benign/Malignant (depuis classification-service)\n"
        "- birads_score         : score BI-RADS 0-6\n"
        "- n_stage              : atteinte ganglionnaire N0/N1/N2/N3 (défaut N0)\n"
        "- m_stage              : métastases M0/M1 (défaut M0)"
    ),
)
async def stage(
    diameter_cm:          float          = Form(0.0),
    tnm_stage:            Optional[str]  = Form(None),
    classification_class: Optional[str]  = Form(None),
    birads_score:         Optional[int]  = Form(None),
    n_stage:              str            = Form("N0"),
    m_stage:              str            = Form("M0"),
):
    result = stage_from_pipeline(
        diameter_cm          = diameter_cm,
        tnm_stage            = tnm_stage,
        classification_class = classification_class,
        birads_score         = birads_score,
        n_stage              = n_stage,
        m_stage              = m_stage,
    )

    logger.info("Staging — T=%s N=%s M=%s → Stade %s",
                result.t_stage, result.n_stage, result.m_stage, result.stage)

    return StageResponse(
        prediction_id = str(uuid.uuid4()),
        t_stage       = result.t_stage,
        n_stage       = result.n_stage,
        m_stage       = result.m_stage,
        stage         = result.stage,
        stage_roman   = result.stage_roman,
        description   = result.description,
        treatment     = result.treatment,
        prognosis     = result.prognosis,
        confidence    = result.confidence,
        timestamp     = datetime.utcnow().isoformat(),
    )