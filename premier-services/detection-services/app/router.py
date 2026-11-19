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
import base64
import html
import logging
import uuid
import os
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from PIL import Image

from app.schemas import PredictionResponse, HealthResponse

logger = logging.getLogger("detection.router")

router = APIRouter(prefix="/api/v1", tags=["Detection"])

CLASSIFICATION_SERVICE_URL = os.getenv("CLASSIFICATION_SERVICE_URL", "http://host.docker.internal:8012")
SEGMENTATION_SERVICE_URL   = os.getenv("SEGMENTATION_SERVICE_URL",   "http://host.docker.internal:8013")
BIRADS_SERVICE_URL         = os.getenv("BIRADS_SERVICE_URL",         "http://host.docker.internal:8014")
LOCALIZATION_SERVICE_URL   = os.getenv("LOCALIZATION_SERVICE_URL",   "http://host.docker.internal:8015")
TUMORSIZE_SERVICE_URL      = os.getenv("TUMORSIZE_SERVICE_URL",      "http://host.docker.internal:8016")
ASSEMBLER_SERVICE_URL      = os.getenv("ASSEMBLER_SERVICE_URL",      "http://host.docker.internal:8018")
VISUALIZATION_SERVICE_URL  = os.getenv("VISUALIZATION_SERVICE_URL",  "http://host.docker.internal:8019")
NARRATIVE_SERVICE_URL      = os.getenv("NARRATIVE_SERVICE_URL",      "http://host.docker.internal:8020")


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


def _image_data_url(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


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
        # Envoie le masque UNIQUEMENT si disponible et non vide
        mask = (segmentation or {}).get("mask_base64", "")
        files = {"file": (filename, _image_to_bytes(image), "image/jpeg")}
        data  = {"mask_base64": mask} if mask else {}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{LOCALIZATION_SERVICE_URL}/api/v1/localize",
                data=data,
                files=files,
            )
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Localisation : %s (%s)", d["quadrant"], d["quadrant_fr"])
                return d
    except Exception as e:
        logger.warning("⚠️ Localisation indisponible : %s", e)
    return None

async def _tumorsize(filename, image: Image.Image, segmentation) -> dict | None:
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


async def _visualize(image, filename, prediction_id, segmentation, include_images: bool = False) -> dict | None:
    def _visualization_payload(include_mask: bool = True) -> dict:
        payload = {}
        if prediction_id:
            payload["prediction_id"] = prediction_id
        if include_mask and (segmentation or {}).get("mask_base64"):
            payload["mask_base64"] = segmentation["mask_base64"]
        if (segmentation or {}).get("tumor_area_pct") is not None:
            payload["tumor_area_pct"] = str(segmentation["tumor_area_pct"])
        payload["include_images"] = "true" if include_images else "false"
        return payload

    async def _post_visualization(data: dict, timeout: float) -> dict | None:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{VISUALIZATION_SERVICE_URL}/api/v1/visualize",
                data=data,
                files={"file": (filename, _image_to_bytes(image), "image/jpeg")},
            )
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Visualization : %s focus=%.2f", d["method"], d["focus_score"])
                return d
        return None

    try:
        return await _post_visualization(
            _visualization_payload(include_mask=True),
            timeout=90.0 if include_images else 45.0,
        )
    except httpx.TimeoutException:
        logger.warning("⚠️ Visualization trop lente")
    except Exception as e:
        logger.warning("⚠️ Visualization indisponible : %s", e)
    return None


def _gradcam_html(filename: str, detection: dict, original_url: str, visualization: dict | None) -> str:
    safe_name = html.escape(filename)
    predicted = html.escape(str(detection.get("predicted_class", "Unknown")))
    confidence = float(detection.get("confidence", 0.0))
    overlay = (visualization or {}).get("overlay_base64")
    heatmap = (visualization or {}).get("heatmap_base64")
    lesion = (visualization or {}).get("lesion_base64")
    method = html.escape(str((visualization or {}).get("method", "gradcam")))
    focus = (visualization or {}).get("focus_score")
    tumor_area = (visualization or {}).get("tumor_area_pct")
    bbox = (visualization or {}).get("lesion_bbox")
    focus_label = "N/A" if focus is None else f"{float(focus):.4f}"
    tumor_area_label = "N/A" if tumor_area is None else f"{float(tumor_area):.4f}%"
    bbox_label = "N/A" if bbox is None else html.escape(str(bbox))

    if predicted != "Cancer":
        body = f"""
        <section class="status ok">
          <h2>Resultat : {predicted}</h2>
          <p>Confiance : {confidence:.2%}. Le pipeline n'a pas lance le Grad-CAM car l'image n'est pas classee cancereuse.</p>
        </section>
        <div class="grid single"><figure><img src="{original_url}" alt="Mammographie originale"><figcaption>Image originale</figcaption></figure></div>
        """
    elif overlay and heatmap:
        lesion_figure = ""
        if lesion:
            lesion_figure = f"""
          <figure><div class="media lesion"><img src="data:image/png;base64,{lesion}" alt="Zoom de la zone suspecte"></div><figcaption>Zone suspecte</figcaption></figure>
            """
        body = f"""
        <div class="grid">
          <figure><div class="media"><img src="{original_url}" alt="Mammographie originale"></div><figcaption>Image originale</figcaption></figure>
          <figure><div class="media"><img src="data:image/png;base64,{overlay}" alt="Grad-CAM overlay"></div><figcaption>Mammographie + Grad-CAM</figcaption></figure>
          <figure><div class="media heatmap"><img src="data:image/png;base64,{heatmap}" alt="Heatmap Grad-CAM"></div><figcaption>Heatmap Grad-CAM</figcaption></figure>
          {lesion_figure}
        </div>
        """
    else:
        body = f"""
        <section class="status warn">
          <h2>Resultat : Cancer</h2>
          <p>Confiance : {confidence:.2%}. La visualisation Grad-CAM n'a pas ete generee par le service.</p>
        </section>
        <div class="grid single"><figure><img src="{original_url}" alt="Mammographie originale"><figcaption>Image originale</figcaption></figure></div>
        """

    return f"""
    <!doctype html>
    <html lang="fr">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Grad-CAM mammographie - {safe_name}</title>
      <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: Arial, sans-serif; background: #f8f8f6; color: #202124; }}
        header {{ padding: 24px 32px 14px; border-bottom: 1px solid #ddd; background: #fff; }}
        h1 {{ margin: 0 0 6px; font-size: 26px; line-height: 1.2; }}
        .file {{ color: #5f6368; }}
        main {{ padding: 24px 32px 40px; }}
        .status {{ padding: 16px 18px; border-radius: 8px; margin-bottom: 26px; border: 1px solid #ddd; background: #fff; }}
        .status h2 {{ margin: 0 0 8px; font-size: 20px; line-height: 1.25; }}
        .status p {{ margin: 0; line-height: 1.55; overflow-wrap: anywhere; }}
        .cancer {{ border-color: #e53935; background: #fff5f5; }}
        .ok {{ border-color: #188038; background: #f1f8f3; }}
        .warn {{ border-color: #b06000; background: #fff8e8; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 22px; align-items: start; }}
        .grid.single {{ max-width: 520px; }}
        figure {{ margin: 0; background: #fff; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        .media {{ aspect-ratio: 2 / 3; width: 100%; max-height: 760px; background: #050505; display: flex; align-items: center; justify-content: center; }}
        .media.heatmap {{ background: #061eea; }}
        .media.lesion img {{ object-fit: cover; }}
        .media img {{ width: 100%; height: 100%; object-fit: contain; display: block; image-rendering: auto; }}
        figure > img {{ width: 100%; aspect-ratio: 2 / 3; max-height: 760px; object-fit: contain; display: block; background: #050505; image-rendering: auto; }}
        figcaption {{ padding: 12px 14px; font-weight: 700; font-size: 18px; border-top: 1px solid #eee; }}
        @media (max-width: 1280px) {{
          .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        }}
        @media (max-width: 720px) {{
          header {{ padding: 18px 16px 12px; }}
          main {{ padding: 18px 16px 28px; }}
          h1 {{ font-size: 23px; }}
          .grid {{ grid-template-columns: 1fr; gap: 16px; }}
          figcaption {{ font-size: 16px; }}
        }}
      </style>
    </head>
    <body>
      <header>
        <h1>Visualisation Grad-CAM</h1>
        <div class="file">{safe_name}</div>
      </header>
      <main>{body}</main>
    </body>
    </html>
    """


async def _assemble(prediction_id, filename, detection, classification, segmentation, birads, localization, tumorsize, visualization) -> dict | None:
    try:
        payload = {
            "prediction_id": prediction_id,
            "filename": filename,
            "detection": detection,
            "classification": classification,
            "segmentation": segmentation,
            "birads": birads,
            "localization": localization,
            "tumorsize": tumorsize,
            "visualization": visualization,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ASSEMBLER_SERVICE_URL}/api/v1/assemble", json=payload)
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Assembler : %s stage=%s", d["status"], (d.get("stage") or {}).get("stage"))
                return d
    except Exception as e:
        logger.warning("⚠️ Assembler indisponible : %s", e)
    return None


async def _narrative(assembler_report) -> dict | None:
    if not assembler_report:
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{NARRATIVE_SERVICE_URL}/api/v1/narrative",
                json={"report": assembler_report, "language": "fr"},
            )
            if r.status_code == 200:
                d = r.json()
                logger.info("✅ Narrative : %s", d["title"])
                return d
    except Exception as e:
        logger.warning("⚠️ Narrative indisponible : %s", e)
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    predictor    = getattr(request.app.state, "predictor", None)
    model_loaded = predictor is not None and predictor.is_loaded
    return HealthResponse(status="ok" if model_loaded else "degraded",
                          model_loaded=model_loaded,
                          timestamp=datetime.utcnow().isoformat())


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Pipeline complet JSON - une seule mammographie",
    description=(
        "Uploader la mammographie une seule fois ici. Le detection-service appelle ensuite "
        "classification, segmentation, BI-RADS, localisation, taille tumorale, assemblage, "
        "narratif et visualisation, puis retourne le resultat complet en JSON."
    ),
)
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

    prediction_id = str(uuid.uuid4())
    classification = segmentation = localization = tumorsize = visualization = assembler_report = narrative = stage = None

    if result["class"] == "Cancer":
        classification = await _classify(image, fname)
        segmentation   = await _segment(image, fname)
        localization   = await _localize(image, fname, segmentation)
        tumorsize      = await _tumorsize(fname, image, segmentation)
        visualization  = await _visualize(image, fname, prediction_id, segmentation, include_images=True)

    birads = await _birads(result["class"], result["confidence"],
                           classification, segmentation, image, fname)

    detection_payload = {
        "prediction_id": prediction_id,
        "filename": fname,
        "predicted_class": result["class"],
        "confidence": round(result["confidence"], 4),
        "probabilities": {k: round(v, 4) for k, v in result["probabilities"].items()},
    }
    assembler_report = await _assemble(
        prediction_id, fname, detection_payload, classification, segmentation,
        birads, localization, tumorsize, visualization,
    )
    stage = (assembler_report or {}).get("stage")
    narrative = await _narrative(assembler_report)

    return PredictionResponse(
        prediction_id   = prediction_id,
        filename        = fname,
        predicted_class = result["class"],
        confidence      = round(result["confidence"], 4),
        probabilities   = {k: round(v, 4) for k, v in result["probabilities"].items()},
        classification  = classification,
        segmentation    = segmentation,
        birads          = birads,
        localization    = localization,
        tumorsize       = tumorsize,
        visualization   = visualization,
        assembler_report = assembler_report,
        stage           = stage,
        narrative       = narrative,
        timestamp       = datetime.utcnow().isoformat(),
    )


@router.post(
    "/predict/gradcam",
    response_class=HTMLResponse,
    summary="Tester tous les services + Grad-CAM - une seule mammographie",
    description=(
        "Endpoint recommande dans Swagger pour ton test complet: uploader une seule "
        "mammographie. Le pipeline appelle tous les services et retourne la page HTML "
        "de visualisation Grad-CAM avec image originale, overlay, heatmap et zone suspecte."
    ),
)
async def predict_gradcam(request: Request,
                          file: UploadFile = File(...)):
    predictor = _get_predictor(request)

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"Type non supporte : {file.content_type}")

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide.")

    image = _read_image(raw)
    fname = file.filename or "image.jpg"
    result = predictor.predict(image)
    prediction_id = str(uuid.uuid4())
    classification = segmentation = localization = tumorsize = visualization = None

    detection_payload = {
        "prediction_id": prediction_id,
        "filename": fname,
        "predicted_class": result["class"],
        "confidence": round(result["confidence"], 4),
        "probabilities": {k: round(v, 4) for k, v in result["probabilities"].items()},
    }

    if result["class"] == "Cancer":
        classification = await _classify(image, fname)
        segmentation = await _segment(image, fname)
        localization = await _localize(image, fname, segmentation)
        tumorsize = await _tumorsize(fname, image, segmentation)
        visualization = await _visualize(
            image,
            fname,
            prediction_id,
            segmentation,
            include_images=True,
        )

    birads = await _birads(
        result["class"],
        result["confidence"],
        classification,
        segmentation,
        image,
        fname,
    )
    assembler_report = await _assemble(
        prediction_id,
        fname,
        detection_payload,
        classification,
        segmentation,
        birads,
        localization,
        tumorsize,
        visualization,
    )
    await _narrative(assembler_report)

    return HTMLResponse(
        _gradcam_html(fname, detection_payload, _image_data_url(image), visualization)
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

        prediction_id = str(uuid.uuid4())
        classification = segmentation = localization = tumorsize = visualization = assembler_report = narrative = stage = None

        if result["class"] == "Cancer":
            classification = await _classify(image, fname)
            segmentation   = await _segment(image, fname)
            localization   = await _localize(image, fname, segmentation)
            tumorsize      = await _tumorsize(fname, image, segmentation)
            visualization  = await _visualize(image, fname, prediction_id, segmentation, include_images=True)

        birads = await _birads(result["class"], result["confidence"],
                               classification, segmentation, image, fname)

        detection_payload = {
            "prediction_id": prediction_id,
            "filename": fname,
            "predicted_class": result["class"],
            "confidence": round(result["confidence"], 4),
            "probabilities": {k: round(v, 4) for k, v in result["probabilities"].items()},
        }
        assembler_report = await _assemble(
            prediction_id, fname, detection_payload, classification, segmentation,
            birads, localization, tumorsize, visualization,
        )
        stage = (assembler_report or {}).get("stage")
        narrative = await _narrative(assembler_report)

        responses.append(PredictionResponse(
            prediction_id   = prediction_id,
            filename        = fname,
            predicted_class = result["class"],
            confidence      = round(result["confidence"], 4),
            probabilities   = {k: round(v, 4) for k, v in result["probabilities"].items()},
            classification  = classification,
            segmentation    = segmentation,
            birads          = birads,
            localization    = localization,
            tumorsize       = tumorsize,
            visualization   = visualization,
            assembler_report = assembler_report,
            stage           = stage,
            narrative       = narrative,
            timestamp       = datetime.utcnow().isoformat(),
        ))

    return responses
