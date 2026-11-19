"""
router.py
Endpoints FastAPI pour la detection du cancer mammaire.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from app.predictor import predictor
from app.schemas import PredictionResponse, HealthResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".dcm"}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Vérifier l'état du service"
)
def health():
    return HealthResponse(
        status="ok",
        model="ResNet50",
        version="1.0.0"
    )


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Prédire Cancer ou Non-Cancer",
    description="""
    Envoie une image mammographique (JPEG, PNG ou DICOM).
    Retourne :
    - **label** : Cancer ou Non-Cancer
    - **confidence** : score de confiance (0 à 1)
    - **probabilities** : probabilités pour chaque classe
    """
)
async def predict(file: UploadFile = File(..., description="Image mammographique (JPEG/PNG/DCM)")):

    # Vérifier l'extension
    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {ext}. Utilisez : {ALLOWED_EXTENSIONS}"
        )

    # Lire les bytes
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    # Prédiction
    try:
        result = predictor.predict(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PredictionResponse(**result)