from pydantic import BaseModel
from typing import Optional

class OutputDetection(BaseModel):
    image_id: Optional[str]
    prediction: str
    confidence: float
    status: str