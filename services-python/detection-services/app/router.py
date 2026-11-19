"""
Routeur FastAPI — Pipeline complet 7 services
1. Detection      → Cancer / Non-Cancer
2. Classification → Benign / Malignant (si Cancer)
3. Segmentation   → masque zone tumorale (si Cancer)
4. BI-RADS        → score 0-6 ACR 2024 (toujours)
5. Localization   → quadrant tumeur (si Cancer)
6. TumorSize      → taille en cm + TNM (si Cancer)
7. Stage          → stade TNM I-IV (si Cancer)
"""
import io
import logging
import uuid
import os
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from PIL import Image

from app.schemas import PredictionResponse, HealthResponse

logger = logging.getLogger("detection.router")

router = APIRouter(prefix="/api/v1", tags=["Detection"])

CLASSIFICATION_SERVICE_URL = os.getenv("CLASSIFICATION_SERVICE_URL", "http://host.docker.internal:8012")
SEGMENTATION_SERVICE_URL   = os.getenv("SEGMENTATION_SERVICE_URL",   "http://host.docker.internal:8013")
BIRADS_SERVICE_URL         = os.getenv("BIRADS_SERVICE_URL",         "http://host.docker.internal:8014")
LOCALIZATION_SERVICE_URL   = os.getenv("LOCALIZATION_SERVICE_URL",   "http://host.docker.internal:8015")
TUMORSIZE_SERVICE_URL      = os.getenv("TUMORSIZE_SERVICE_URL",      "http://host.docker.internal:8016")
STAGE_SERVICE_URL          = os.getenv("STAGE_SERVICE_URL",          "http://host.docker.internal:8017")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_predictor(request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None or not predictor.is_loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Modèle non chargé.")
    return predictor


def _read_image(data: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Image invalide : {exc}")


def _image_to_bytes(image: Image.Image) -> io.BytesIO:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    buf.seek(0)
    return buf


# ── Service calls ─────────────────────────────────────────────────────────────

async def _classify(image: Image.Image, filename: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{CLASSIFICATION_SERVICE_URL}/api/v1/classify",
                                  files={"file": (filename, _image_to_bytes(image), "image/jpeg")})
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Classification : %s (%.2f)", d["predicted_class"], d["confidence"])
                return d
    except Exception as e:
        logger.warning("⚠️ Classification indisponible : %s", e)
    return None


async def _segment(image: Image.Image, filename: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{SEGMENTATION_SERVICE_URL}/api/v1/segment",
                                  files={"file": (filename, _image_to_bytes(image), "image/jpeg")})
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Segmentation : %d px (%.2f%%)", d["tumor_area_px"], d["tumor_area_pct"])
                return d
    except Exception as e:
        logger.warning("⚠️ Segmentation indisponible : %s", e)
    return None


async def _birads(detection_class, detection_conf, classification, segmentation, image, filename) -> dict | None:
    try:
        data = {"detection_class": detection_class, "detection_conf": str(detection_conf)}
        if (classification or {}).get("predicted_class"):
            data["classification_class"] = classification["predicted_class"]
        if (classification or {}).get("confidence"):
            data["classification_conf"] = str(classification["confidence"])
        if (segmentation or {}).get("tumor_area_pct"):
            data["tumor_area_pct"] = str(segmentation["tumor_area_pct"])
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{BIRADS_SERVICE_URL}/api/v1/birads", data=data,
                                  files={"file": (filename, _image_to_bytes(image), "image/jpeg")})
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ BI-RADS %s (%s)", d["birads_score"], d["birads_category"])
                return d
    except Exception as e:
        logger.warning("⚠️ BI-RADS indisponible : %s", e)
    return None


async def _localize(image, filename, segmentation) -> dict | None:
    try:
        data = {}
        if (segmentation or {}).get("mask_base64"):
            data["mask_base64"] = segmentation["mask_base64"]
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{LOCALIZATION_SERVICE_URL}/api/v1/localize", data=data,
                                  files={"file": (filename, _image_to_bytes(image), "image/jpeg")})
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Localisation : %s (%s)", d["quadrant"], d["quadrant_fr"])
                return d
    except Exception as e:
        logger.warning("⚠️ Localisation indisponible : %s", e)
    return None


async def _tumorsize(filename, segmentation) -> dict | None:
    try:
        data = {"filename": filename}
        if (segmentation or {}).get("mask_base64"):
            data["mask_base64"] = segmentation["mask_base64"]
        elif (segmentation or {}).get("tumor_area_pct") is not None:
            data["tumor_area_pct"] = str(segmentation["tumor_area_pct"])
        else:
            return None
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{TUMORSIZE_SERVICE_URL}/api/v1/size", data=data)
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ TumorSize : %.2f cm (%s)", d["diameter_cm"], d["tnm_stage"])
                return d
    except Exception as e:
        logger.warning("⚠️ TumorSize indisponible : %s", e)
    return None


async def _stage(classification, birads, tumorsize) -> dict | None:
    try:
        data = {}
        if (tumorsize or {}).get("diameter_cm"):
            data["diameter_cm"] = str(tumorsize["diameter_cm"])
        if (tumorsize or {}).get("tnm_stage"):
            data["tnm_stage"] = tumorsize["tnm_stage"]
        if (classification or {}).get("predicted_class"):
            data["classification_class"] = classification["predicted_class"]
        if (birads or {}).get("birads_score") is not None:
            data["birads_score"] = str(birads["birads_score"])
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{STAGE_SERVICE_URL}/api/v1/stage", data=data)
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Stage : %s (%s)", d["stage"], d["stage_roman"])
                return d
    except Exception as e:
        logger.warning("⚠️ Stage indisponible : %s", e)
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    predictor    = getattr(request.app.state, "predictor", None)
    model_loaded = predictor is not None and predictor.is_loaded
    return HealthResponse(status="ok" if model_loaded else "degraded",
                          model_loaded=model_loaded,
                          timestamp=datetime.utcnow().isoformat())


@router.post("/predict", response_model=PredictionResponse,
             summary="Pipeline complet 7 services")
async def predict(request: Request,
                  file: UploadFile = File(...)):
    predictor = _get_predictor(request)

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"Type non supporté : {file.content_type}")

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide.")

    image  = _read_image(raw)
    result = predictor.predict(image)
    fname  = file.filename or "image.jpg"

    logger.info("Détection — classe=%s  confiance=%.4f  fichier=%s",
                result["class"], result["confidence"], fname)

    classification = segmentation = localization = tumorsize = stage = None

    if result["class"] == "Cancer":
        classification = await _classify(image, fname)
        segmentation   = await _segment(image, fname)
        localization   = await _localize(image, fname, segmentation)
        tumorsize      = await _tumorsize(fname, segmentation)

    birads = await _birads(result["class"], result["confidence"],
                           classification, segmentation, image, fname)

    if result["class"] == "Cancer":
        stage = await _stage(classification, birads, tumorsize)

    return PredictionResponse(
        prediction_id   = str(uuid.uuid4()),
        filename        = fname,
        predicted_class = result["class"],
        confidence      = round(result["confidence"], 4),
        probabilities   = {k: round(v, 4) for k, v in result["probabilities"].items()},
        classification  = classification,
        segmentation    = segmentation,
        birads          = birads,
        localization    = localization,
        tumorsize       = tumorsize,
        stage           = stage,
        timestamp       = datetime.utcnow().isoformat(),
    )


@router.post("/predict/batch", response_model=list[PredictionResponse],
             summary="Pipeline complet sur plusieurs images")
async def predict_batch(request: Request, files: list[UploadFile] = File(...)):
    if len(files) > 16:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Maximum 16 images par batch.")

    predictor = _get_predictor(request)
    responses = []

    for file in files:
        raw    = await file.read()
        image  = _read_image(raw)
        result = predictor.predict(image)
        fname  = file.filename or "image.jpg"

        classification = segmentation = localization = tumorsize = stage = None

        if result["class"] == "Cancer":
            classification = await _classify(image, fname)
            segmentation   = await _segment(image, fname)
            localization   = await _localize(image, fname, segmentation)
            tumorsize      = await _tumorsize(fname, segmentation)

        birads = await _birads(result["class"], result["confidence"],
                               classification, segmentation, image, fname)

        if result["class"] == "Cancer":
            stage = await _stage(classification, birads, tumorsize)

        responses.append(PredictionResponse(
            prediction_id   = str(uuid.uuid4()),
            filename        = fname,
            predicted_class = result["class"],
            confidence      = round(result["confidence"], 4),
            probabilities   = {k: round(v, 4) for k, v in result["probabilities"].items()},
            classification  = classification,
            segmentation    = segmentation,
            birads          = birads,
            localization    = localization,
            tumorsize       = tumorsize,
            stage           = stage,
            timestamp       = datetime.utcnow().isoformat(),
        ))

    return responses