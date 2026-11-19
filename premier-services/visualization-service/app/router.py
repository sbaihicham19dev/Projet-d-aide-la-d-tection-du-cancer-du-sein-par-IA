import io
import asyncio
import base64
import html
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from PIL import Image

from app.schemas import HealthResponse, VisualizationResponse

router = APIRouter(prefix="/api/v1", tags=["Visualization"])


def _image_data_url(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _visualization_html(filename: str, original_url: str, result: dict, predicted_class: str) -> str:
    safe_name = html.escape(filename)
    safe_class = html.escape(predicted_class or "Cancer")
    overlay = result.get("overlay_base64")
    heatmap = result.get("heatmap_base64")
    lesion = result.get("lesion_base64")
    method = html.escape(str(result.get("method", "gradcam")))
    focus = result.get("focus_score")
    tumor_area = result.get("tumor_area_pct")
    bbox = result.get("lesion_bbox")
    focus_label = "N/A" if focus is None else f"{float(focus):.4f}"
    tumor_area_label = "N/A" if tumor_area is None else f"{float(tumor_area):.4f}%"
    bbox_label = "N/A" if bbox is None else html.escape(str(bbox))

    if safe_class.lower() not in {"cancer", "malignant"}:
        body = f"""
        <section class="status ok">
          <h2>Resultat : {safe_class}</h2>
          <p>Grad-CAM non affiche car l'image n'est pas indiquee comme cancereuse.</p>
        </section>
        <div class="grid single">
          <figure><img src="{original_url}" alt="Mammographie originale"><figcaption>Image originale</figcaption></figure>
        </div>
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
          <figure><div class="media"><img src="data:image/png;base64,{overlay}" alt="Mammographie avec Grad-CAM"></div><figcaption>Mammographie + Grad-CAM</figcaption></figure>
          <figure><div class="media heatmap"><img src="data:image/png;base64,{heatmap}" alt="Heatmap Grad-CAM"></div><figcaption>Heatmap Grad-CAM</figcaption></figure>
          {lesion_figure}
        </div>
        """
    else:
        body = f"""
  
        <div class="grid single">
          <figure><img src="{original_url}" alt="Mammographie originale"><figcaption>Image originale</figcaption></figure>
        </div>
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
        .grid.single {{ max-width: 560px; }}
        figure {{ margin: 0; background: #fff; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        # Après ✅ — taille naturelle de l'image
        .media {{ width: 100%; background: #050505; display: flex; align-items: center; justify-content: center; }}
        .media.heatmap {{ background: #061eea; }}
        .media img {{ width: 100%; height: auto; object-fit: contain; display: block; }}
        figure > img {{ width: 100%; height: auto; object-fit: contain; display: block; background: #050505; }}
        figure > img {{ width: 100%; aspect-ratio: 2 / 3; max-height: 760px; object-fit: contain; display: block; background: #050505; }}
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


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _clean_optional_float(value: Optional[str]) -> Optional[float]:
    value = _clean_optional_text(value)
    if value is None:
        return None
    return float(value)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service="visualization-service", timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/visualize/ui", response_class=HTMLResponse)
async def visualize_ui():
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="fr">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Visualisation Grad-CAM</title>
          <style>
            body { margin: 0; font-family: Arial, sans-serif; background: #f8f8f6; color: #202124; }
            header { padding: 24px 32px 12px; border-bottom: 1px solid #ddd; background: #fff; }
            h1 { margin: 0 0 6px; font-size: 24px; }
            main { padding: 24px 32px 40px; max-width: 720px; }
            form { display: grid; gap: 16px; padding: 18px; border: 1px solid #ddd; border-radius: 8px; background: #fff; }
            label { display: grid; gap: 6px; font-weight: 700; }
            input, button { font: inherit; }
            input[type="file"], input[type="text"], input[type="number"] { padding: 10px; border: 1px solid #bbb; border-radius: 6px; }
            button { width: fit-content; padding: 10px 16px; border: 0; border-radius: 6px; background: #1a73e8; color: #fff; font-weight: 700; cursor: pointer; }
          </style>
        </head>
        <body>
          <header>
            <h1>Visualisation Grad-CAM</h1>
            <div>Uploader une mammographie pour afficher l'originale, l'overlay Grad-CAM et la heatmap.</div>
          </header>
          <main>
            <form method="post" action="/api/v1/visualize/view" enctype="multipart/form-data">
              <label>
                Mammographie
                <input name="file" type="file" accept="image/*" required>
              </label>
              <label>
                Classe predite
                <input name="predicted_class" type="text" value="Cancer">
              </label>
              <label>
                Masque base64
                <input name="mask_base64" type="text" placeholder="optionnel">
              </label>
              <label>
                Surface tumeur %
                <input name="tumor_area_pct" type="number" step="0.0001" placeholder="optionnel">
              </label>
              <button type="submit">Afficher Grad-CAM</button>
            </form>
          </main>
        </body>
        </html>
        """
    )


@router.post("/visualize", response_model=VisualizationResponse)
async def visualize(
    request: Request,
    file: UploadFile = File(...),
    prediction_id: Optional[str] = Form(None),
    mask_base64: Optional[str] = Form(None),
    tumor_area_pct: Optional[float] = Form(None),
    include_images: bool = Form(True),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}")

    result = request.app.state.visualizer.visualize(image, mask_base64, tumor_area_pct, include_images=include_images)
    response = VisualizationResponse(
        prediction_id=prediction_id or str(uuid.uuid4()),
        filename=file.filename or "image.jpg",
        timestamp=datetime.now(timezone.utc).isoformat(),
        **result,
    )
    if os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        try:
            await asyncio.wait_for(request.app.state.publisher.publish(response.model_dump(mode="json")), timeout=1.0)
        except Exception:
            pass
    return response


@router.post("/visualize/view", response_class=HTMLResponse)
async def visualize_view(
    request: Request,
    file: UploadFile = File(...),
    predicted_class: str = Form("Cancer"),
    mask_base64: Optional[str] = Form(None),
    tumor_area_pct: Optional[str] = Form(None),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}")

    include_gradcam = predicted_class.lower() in {"cancer", "malignant"}
    result = {}
    if include_gradcam:
        try:
            parsed_tumor_area_pct = _clean_optional_float(tumor_area_pct)
        except ValueError:
            raise HTTPException(status_code=400, detail="tumor_area_pct must be a number.")
        result = request.app.state.visualizer.visualize(
            image,
            mask_base64=_clean_optional_text(mask_base64),
            tumor_area_pct=parsed_tumor_area_pct,
            include_images=True,
        )

    return HTMLResponse(
        _visualization_html(
            file.filename or "image.jpg",
            _image_data_url(image),
            result,
            predicted_class,
        )
    )
