from fastapi import APIRouter, UploadFile, File
from app.schemas import OutputDetection
from app.predictor import predict
import base64

router = APIRouter()

@router.post("/predict", response_model=OutputDetection)
async def predict_image(file: UploadFile = File(...)):
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")
    result = predict(image_base64)
    return OutputDetection(
        image_id=file.filename,
        prediction=result["prediction"],
        confidence=result["confidence"],
        status="success"
    )