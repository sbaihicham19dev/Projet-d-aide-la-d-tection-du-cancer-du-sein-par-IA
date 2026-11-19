"""
Predictor - ResNet-50 mammography detector.

The checkpoint head uses these weighted layers:
fc.1 Linear(2048,512), fc.2 BN(512), fc.5 Linear(512,128), fc.7 Linear(128,2).
"""

import json
import logging
import os
from collections import OrderedDict
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image

logger = logging.getLogger("detection.predictor")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "resnet50_mammography.pt"
DEFAULT_CLASS_NAMES_PATH = BASE_DIR / "models" / "class_names.json"

MODEL_PATH = Path(os.getenv("DETECTION_MODEL_PATH", "/app/models/resnet50_mammography.pt"))
CLASS_NAMES_PATH = Path(os.getenv("DETECTION_CLASS_NAMES_PATH", "/app/models/class_names.json"))
CANCER_THRESHOLD = float(os.getenv("DETECTION_CANCER_THRESHOLD", "0.40"))

BASE_TRANSFORMS = T.Compose([
    T.Resize((224, 224)),
    T.Grayscale(num_output_channels=3),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

FLIP_TRANSFORMS = T.Compose([
    T.Resize((224, 224)),
    T.RandomHorizontalFlip(p=1.0),
    T.Grayscale(num_output_channels=3),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def build_model(num_classes: int = 2) -> nn.Module:
    model = models.resnet50(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(OrderedDict([
        ("1", nn.Linear(in_features, 512)),
        ("2", nn.BatchNorm1d(512)),
        ("3", nn.ReLU(inplace=True)),
        ("4", nn.Dropout(p=0.5)),
        ("5", nn.Linear(512, 128)),
        ("6", nn.ReLU(inplace=True)),
        ("7", nn.Linear(128, num_classes)),
    ]))
    return model


class Predictor:
    def __init__(self):
        self.model = None
        self.class_names = ["Cancer", "Non-Cancer"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        self.cancer_threshold = CANCER_THRESHOLD

    def _model_path(self) -> Path:
        return MODEL_PATH if MODEL_PATH.exists() else DEFAULT_MODEL_PATH

    def _class_names_path(self) -> Path:
        return CLASS_NAMES_PATH if CLASS_NAMES_PATH.exists() else DEFAULT_CLASS_NAMES_PATH

    def load(self) -> None:
        model_path = self._model_path()
        class_names_path = self._class_names_path()
        logger.info("Chargement du modele depuis %s", model_path)

        try:
            if class_names_path.exists():
                with open(class_names_path, "r") as f:
                    self.class_names = json.load(f)
                logger.info("Classes : %s", self.class_names)

            self.model = build_model(num_classes=len(self.class_names))

            checkpoint = torch.load(model_path, map_location=self.device)
            state = (
                checkpoint.get("model_state_dict")
                or checkpoint.get("state_dict")
                or checkpoint
            )

            missing, unexpected = self.model.load_state_dict(state, strict=False)
            if missing:
                logger.warning("Poids manquants (%d) : %s", len(missing), missing[:5])
            if unexpected:
                logger.warning("Poids inattendus (%d) : %s", len(unexpected), unexpected[:5])
            if not missing and not unexpected:
                logger.info("Tous les poids charges correctement")

            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("Modele charge avec succes")

        except Exception as e:
            logger.error("Erreur chargement modele : %s", e)
            self.model = None
            self.is_loaded = True

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        if self.model is None:
            return {
                "class": "Unknown",
                "confidence": 0.0,
                "is_confident": False,
                "threshold": self.cancer_threshold,
                "probabilities": {"Cancer": 0.5, "Non-Cancer": 0.5},
            }

        tensors = [
            BASE_TRANSFORMS(image).unsqueeze(0).to(self.device),
            FLIP_TRANSFORMS(image).unsqueeze(0).to(self.device),
        ]
        probs = torch.stack([
            torch.softmax(self.model(tensor), dim=1).squeeze(0)
            for tensor in tensors
        ]).mean(dim=0)

        cancer_idx = self.class_names.index("Cancer") if "Cancer" in self.class_names else None
        non_cancer_idx = self.class_names.index("Non-Cancer") if "Non-Cancer" in self.class_names else None

        if cancer_idx is not None and float(probs[cancer_idx]) >= self.cancer_threshold:
            idx = cancer_idx
        elif non_cancer_idx is not None:
            idx = non_cancer_idx
        else:
            idx = int(torch.argmax(probs))

        confidence = float(probs[idx])
        return {
            "class": self.class_names[idx] if idx < len(self.class_names) else "Unknown",
            "confidence": confidence,
            "is_confident": confidence >= self.cancer_threshold,
            "threshold": self.cancer_threshold,
            "probabilities": {
                name: float(probs[i])
                for i, name in enumerate(self.class_names)
            },
        }
