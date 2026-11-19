"""
Router — Classification Service
"""
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from PIL import Image
import io

from app.schemas import ClassificationResponse

logger = logging.getLogger("classification.router")

router = APIRouter(prefix="/api/v1", tags=["Classification"])


@router.get("/health")
async def health():
    return {"status": "ok", "service": "classification-service"}


@router.post("/classify", response_model=ClassificationResponse)
async def classify(request: Request, file: UploadFile = File(...)):
    """
    Classifie une mammographie détectée comme Cancer en :
    - Benign  (bénin)
    - Malignant (malin)
    """
    # Vérification type fichier
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")

    try:
        contents = await file.read()
        image    = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image invalide : {str(e)}")

    # Récupération du classifier depuis le state
    classifier = request.app.state.classifier
    result     = classifier.predict(image)

    return ClassificationResponse(
        prediction_id   = str(uuid.uuid4()),
        filename        = file.filename,
        predicted_class = result["class"],
        confidence      = result["confidence"],
        probabilities   = result["probabilities"],
        timestamp       = datetime.now(timezone.utc),
    )