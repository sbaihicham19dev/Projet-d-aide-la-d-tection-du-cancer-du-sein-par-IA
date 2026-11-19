"""
Router — Localization Service
POST /api/v1/localize → quadrant de la tumeur
"""
import uuid
import io
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from PIL import Image

from app.schemas import LocalizationResponse, HealthResponse

logger = logging.getLogger("localization.router")
router = APIRouter(prefix="/api/v1", tags=["Localization"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    localizer    = getattr(request.app.state, "localizer", None)
    model_loaded = localizer is not None and localizer.is_loaded
    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post(
    "/localize",
    response_model=LocalizationResponse,
    summary="Localisation de la tumeur",
    description=(
        "Localise la tumeur dans le sein.\n\n"
        "2 modes :\n"
        "1. Avec masque base64 (depuis segmentation-service) — plus précis\n"
        "2. Avec image seule — localisation approximative\n\n"
        "Quadrants : UO (Haut Externe), UI (Haut Interne), "
        "LO (Bas Externe), LI (Bas Interne), C (Central)"
    ),
)
async def localize(
    request:     Request,
    file:        UploadFile          = File(...),
    mask_base64: Optional[str]       = Form(None),
    side:        Optional[str]       = Form(None),  # "LEFT" ou "RIGHT"
):
    localizer = getattr(request.app.state, "localizer", None)
    if localizer is None or not localizer.is_loaded:
        raise HTTPException(status_code=503, detail="Service non prêt")

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Image invalide : {e}")

    # Localisation depuis masque ou image directe
    if mask_base64:
        result = localizer.localize_from_mask(mask_base64, side)
    else:
        result = localizer.localize_from_image(image)

    logger.info("Localisation — quadrant=%s  centroïde=(%.2f, %.2f)  fichier=%s",
                result.quadrant, result.centroid_x, result.centroid_y, file.filename)

    return LocalizationResponse(
        prediction_id  = str(uuid.uuid4()),
        filename       = file.filename or "unknown",
        quadrant       = result.quadrant,
        quadrant_name  = result.quadrant_name,
        quadrant_fr    = result.quadrant_fr,
        centroid_x     = result.centroid_x,
        centroid_y     = result.centroid_y,
        centroid_x_px  = result.centroid_x_px,
        centroid_y_px  = result.centroid_y_px,
        tumor_area_pct = result.tumor_area_pct,
        confidence     = result.confidence,
        timestamp      = datetime.utcnow().isoformat(),
    )