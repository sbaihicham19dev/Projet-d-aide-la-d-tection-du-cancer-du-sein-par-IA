"""
Router — TumorSize Service
POST /api/v1/size → taille tumeur en cm
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.schemas import TumorSizeResponse, HealthResponse

logger = logging.getLogger("tumorsize.router")
router = APIRouter(prefix="/api/v1", tags=["TumorSize"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    sizer        = getattr(request.app.state, "sizer", None)
    model_loaded = sizer is not None and sizer.is_loaded
    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post(
    "/size",
    response_model=TumorSizeResponse,
    summary="Calcul taille tumeur",
    description=(
        "Calcule la taille réelle de la tumeur en cm.\n\n"
        "Paramètres :\n"
        "- mask_base64     : masque PNG base64 (depuis segmentation-service)\n"
        "- tumor_area_pct  : % surface tumorale (alternatif au masque)\n"
        "- pixel_spacing_mm: espacement pixels en mm (depuis DICOM, défaut=0.07)\n"
        "- original_size_px: taille image originale en pixels (défaut=224)\n\n"
        "Retourne : dimensions px/cm, surface cm², classification TNM"
    ),
)
async def size(
    request:          Request,
    filename:         str            = Form("image.jpg"),
    mask_base64:      Optional[str]  = Form(None),
    tumor_area_pct:   Optional[float]= Form(None),
    pixel_spacing_mm: float          = Form(0.07),
    original_size_px: int            = Form(224),
):
    sizer = getattr(request.app.state, "sizer", None)
    if sizer is None or not sizer.is_loaded:
        raise HTTPException(status_code=503, detail="Service non prêt")

    if mask_base64:
        result = sizer.calculate_from_mask(
            mask_base64      = mask_base64,
            pixel_spacing_mm = pixel_spacing_mm,
            original_size_px = original_size_px,
        )
    elif tumor_area_pct is not None:
        result = sizer.calculate_from_area_pct(
            tumor_area_pct   = tumor_area_pct,
            pixel_spacing_mm = pixel_spacing_mm,
            original_size_px = original_size_px,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Fournir mask_base64 ou tumor_area_pct"
        )

    logger.info(
        "Taille — %.2f×%.2f cm  diam=%.2f cm  %s  fichier=%s",
        result.width_cm, result.height_cm,
        result.diameter_cm, result.tnm_stage, filename
    )

    return TumorSizeResponse(
        prediction_id    = str(uuid.uuid4()),
        filename         = filename,
        width_px         = result.width_px,
        height_px        = result.height_px,
        area_px          = result.area_px,
        area_pct         = result.area_pct,
        width_cm         = result.width_cm,
        height_cm        = result.height_cm,
        diameter_cm      = result.diameter_cm,
        area_cm2         = result.area_cm2,
        tnm_stage        = result.tnm_stage,
        tnm_desc         = result.tnm_desc,
        pixel_spacing_mm = result.pixel_spacing_mm,
        original_size_px = result.original_size_px,
        timestamp        = datetime.utcnow().isoformat(),
    )