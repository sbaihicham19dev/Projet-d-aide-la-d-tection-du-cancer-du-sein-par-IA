"""
Predictor — version stable (no crash + compatible state_dict mismatch)
"""

import json
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image

logger = logging.getLogger("detection.predictor")

# ───────────────────────────────
# PATHS
# ───────────────────────────────
MODEL_PATH = Path("/app/models/resnet50_mammography.pt")
CLASS_NAMES_PATH = Path("/app/models/class_names.json")

# ───────────────────────────────
# TRANSFORMS
# ───────────────────────────────
TRANSFORMS = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


class Predictor:
    def __init__(self):
        self.model = None
        self.class_names = ["Cancer", "Non-Cancer"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False

    def load(self) -> None:
        logger.info(f"Chargement du modèle depuis {MODEL_PATH}")

        try:
            # ── classes
            if CLASS_NAMES_PATH.exists():
                with open(CLASS_NAMES_PATH, "r") as f:
                    self.class_names = json.load(f)

            # ── model base
            self.model = models.resnet50(weights=None)
            self.model.fc = nn.Linear(self.model.fc.in_features, len(self.class_names))

            # ── load checkpoint
            checkpoint = torch.load(MODEL_PATH, map_location=self.device)

            state = (
                checkpoint.get("model_state_dict")
                or checkpoint.get("state_dict")
                or checkpoint
            )

            self.model.load_state_dict(state, strict=False)

            self.model.to(self.device)
            self.model.eval()

            self.is_loaded = True
            logger.info("✅ Modèle chargé avec succès")

        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            self.model = None
            self.is_loaded = True  # ⚠️ ne pas crash container

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:

        if self.model is None:
            return {
                "class": "Unknown",
                "confidence": 0.0,
                "is_confident": False,
                "threshold": 0.7,
                "probabilities": {"Cancer": 0.5, "Non-Cancer": 0.5}
            }

        tensor = TRANSFORMS(image).unsqueeze(0).to(self.device)

        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        idx = int(torch.argmax(probs))
        confidence = float(probs[idx])

        return {
            "class": self.class_names[idx] if idx < len(self.class_names) else "Unknown",
            "confidence": confidence,
            "is_confident": confidence >= 0.7,
            "threshold": 0.7,
            "probabilities": {
                name: float(probs[i])
                for i, name in enumerate(self.class_names)
            }
        }