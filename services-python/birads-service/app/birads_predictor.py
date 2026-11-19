"""
birads_predictor.py
--------------------
CNN features + règles ACR → score BI-RADS
"""
import logging
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image

from app.acr_rules import compute_birads, BIRADSResult

logger = logging.getLogger("birads.predictor")

BASE_DIR   = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "birads_cnn.pt"
IMG_SIZE   = 224

TRANSFORM = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.Grayscale(num_output_channels=3),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
])


def build_model(num_classes: int = 7) -> nn.Module:
    """ResNet-50 fine-tuné pour 7 classes BI-RADS (0-6)."""
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    for param in model.parameters():
        param.requires_grad = False
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=0.5),
        nn.Linear(in_features, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.3),
        nn.Linear(256, num_classes),
    )
    return model


class BIRADSPredictor:
    def __init__(self):
        self.model     = None
        self.device    = torch.device("cpu")
        self.is_loaded = False
        self.classes   = [0, 1, 2, 3, 4, 5, 6]

    def load(self) -> None:
        logger.info("Chargement BI-RADS CNN depuis %s …", MODEL_PATH)

        if not MODEL_PATH.exists():
            logger.warning("⚠️ birads_cnn.pt introuvable — mode règles ACR uniquement")
            self.is_loaded = True
            return

        try:
            self.model = build_model(num_classes=7)
            state = torch.load(MODEL_PATH, map_location=self.device)
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            self.model.load_state_dict(state)
            self.model.eval()
            self.is_loaded = True
            logger.info("✅ BI-RADS CNN chargé")
        except Exception as e:
            logger.error("❌ Erreur chargement : %s", e)
            self.model     = None
            self.is_loaded = True

    @torch.no_grad()
    def predict_from_pipeline(
        self,
        image:                Image.Image,
        detection_class:      str,
        detection_conf:       float,
        classification_class: Optional[str]   = None,
        classification_conf:  Optional[float] = None,
        tumor_area_pct:       Optional[float] = None,
    ) -> dict:
        """
        Calcule le score BI-RADS depuis les résultats du pipeline.
        Si le CNN est chargé → combine CNN + règles ACR.
        Sinon → règles ACR uniquement.
        """
        # Règles ACR
        result = compute_birads(
            detection_class      = detection_class,
            detection_conf       = detection_conf,
            classification_class = classification_class,
            classification_conf  = classification_conf,
            tumor_area_pct       = tumor_area_pct,
        )

        # Si CNN disponible → ajuste le score avec les prédictions CNN
        cnn_score = None
        if self.model is not None and image is not None:
            tensor    = TRANSFORM(image).unsqueeze(0).to(self.device)
            logits    = self.model(tensor)
            probs     = torch.softmax(logits, dim=1).squeeze(0)
            cnn_score = int(probs.argmax().item())
            cnn_conf  = float(probs[cnn_score].item())

            # Combine CNN + règles ACR (moyenne pondérée)
            combined_score = round((result.score * 0.6 + cnn_score * 0.4))
            result.score      = max(0, min(6, combined_score))
            result.confidence = round((result.confidence + cnn_conf) / 2, 3)

        return {
            "birads_score":      result.score,
            "birads_category":   result.category,
            "description":       result.description,
            "malignancy_risk":   result.malignancy_risk,
            "recommendation":    result.recommendation,
            "confidence":        result.confidence,
            "cnn_score":         cnn_score,
            "method":            "CNN+ACR" if cnn_score is not None else "ACR_rules",
        }