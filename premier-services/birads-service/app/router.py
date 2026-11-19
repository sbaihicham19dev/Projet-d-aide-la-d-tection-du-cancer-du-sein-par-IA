"""
Router — BI-RADS Service
POST /api/v1/birads → score BI-RADS 0-6
"""
import uuid
import logging
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from PIL import Image

from app.schemas import BIRADSResponse, HealthResponse

logger = logging.getLogger("birads.router")
router = APIRouter(prefix="/api/v1", tags=["BI-RADS"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    predictor    = getattr(request.app.state, "predictor", None)
    model_loaded = predictor is not None and predictor.is_loaded
    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post(
    "/birads",
    response_model=BIRADSResponse,
    summary="Score BI-RADS",
    description=(
        "Calcule le score BI-RADS (0-6) depuis les résultats du pipeline.\n\n"
        "Paramètres :\n"
        "- detection_class : 'Cancer' ou 'Non-Cancer'\n"
        "- detection_conf  : confiance détection (0-1)\n"
        "- classification_class : 'Benign' ou 'Malignant' (optionnel)\n"
        "- classification_conf  : confiance classification (0-1)\n"
        "- tumor_area_pct : % surface tumorale (optionnel)\n"
        "- file : image mammographique (optionnel, pour CNN)"
    ),
)
async def birads(
    request:              Request,
    detection_class:      str            = Form(...),
    detection_conf:       float          = Form(...),
    classification_class: Optional[str]  = Form(None),
    classification_conf:  Optional[float]= Form(None),
    tumor_area_pct:       Optional[float]= Form(None),
    file: Optional[UploadFile]           = File(None),
):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None or not predictor.is_loaded:
        raise HTTPException(status_code=503, detail="Service non prêt")

    # Image optionnelle pour CNN
    image = None
    if file is not None:
        try:
            raw   = await file.read()
            image = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as e:
            logger.warning("⚠️ Image invalide : %s", e)

    result = predictor.predict_from_pipeline(
        image                = image,
        detection_class      = detection_class,
        detection_conf       = detection_conf,
        classification_class = classification_class,
        classification_conf  = classification_conf,
        tumor_area_pct       = tumor_area_pct,
    )

    logger.info("BI-RADS %s (%s) — %s",
                result["birads_score"], result["birads_category"], result["method"])

    return BIRADSResponse(
        prediction_id   = str(uuid.uuid4()),
        birads_score    = result["birads_score"],
        birads_category = result["birads_category"],
        description     = result["description"],
        malignancy_risk = result["malignancy_risk"],
        recommendation  = result["recommendation"],
        confidence      = result["confidence"],
        method          = result["method"],
        timestamp       = datetime.utcnow().isoformat(),
    )