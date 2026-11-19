"""
Router — Segmentation Service
POST /api/v1/segment → masque PNG base64 + stats tumeur
"""
import io
import uuid
import base64
import logging
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from PIL import Image

from app.schemas import SegmentationResponse, HealthResponse

logger = logging.getLogger("segmentation.router")

router = APIRouter(prefix="/api/v1", tags=["Segmentation"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    segmentor    = getattr(request.app.state, "segmentor", None)
    model_loaded = segmentor is not None and segmentor.is_loaded
    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post(
    "/segment",
    response_model=SegmentationResponse,
    summary="Segmentation de tumeur",
    description=(
        "Envoie une image mammographique et reçoit : "
        "masque PNG (base64), surface tumeur en pixels et pourcentage."
    ),
)
async def segment(
    request: Request,
    file: UploadFile = File(..., description="Image mammographique (JPEG ou PNG)"),
):
    segmentor = getattr(request.app.state, "segmentor", None)
    if segmentor is None or not segmentor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle non chargé — réessayez dans quelques secondes.",
        )

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Type non supporté : {file.content_type}",
        )

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier vide.",
        )

    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image invalide : {e}",
        )

    # Segmentation
    result = segmentor.segment(image)

    # Encode masque en base64
    buf = io.BytesIO()
    result["mask_image"].save(buf, format="PNG")
    mask_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    logger.info(
        "Segmentation — tumeur=%d px (%.2f%%)  fichier=%s",
        result["tumor_area_px"],
        result["tumor_area_pct"],
        file.filename,
    )

    return SegmentationResponse(
        prediction_id  = str(uuid.uuid4()),
        filename       = file.filename or "unknown",
        mask_base64    = mask_b64,
        tumor_area_px  = result["tumor_area_px"],
        tumor_area_pct = result["tumor_area_pct"],
        width          = 224,
        height         = 224,
        timestamp      = datetime.utcnow().isoformat(),
    )