"""
Classifier — Chargement EfficientNet-B4 et inférence Bénin/Malin
"""
import json
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image

logger = logging.getLogger("classification.classifier")

BASE_DIR        = Path(__file__).resolve().parent.parent
MODEL_PATH      = BASE_DIR / "models" / "efficientnet_b4.pt"
CLASS_NAMES_PATH = BASE_DIR / "models" / "class_names.json"

# ── Transform (même normalisation qu'à l'entraînement) ───────────────────────
TRANSFORMS = T.Compose([
    T.Resize(380),
    T.CenterCrop(380),
    T.Grayscale(num_output_channels=3),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
])


def build_model(num_classes: int) -> nn.Module:
    """Construit EfficientNet-B4 avec tête custom identique à l'entraînement."""
    try:
        from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights
        model = efficientnet_b4(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes),
        )
    except Exception:
        # Fallback ResNet-50 si EfficientNet non disponible
        from torchvision.models import resnet50
        model = resnet50(weights=None)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes),
        )
    return model


class Classifier:
    def __init__(self):
        self.model       = None
        self.class_names = ["Benign", "Malignant"]
        self.device      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded   = False

    # ── LOAD ──────────────────────────────────────────────────────────────────
    def load(self) -> None:
        logger.info("Chargement du modèle depuis %s …", MODEL_PATH)

        # Chargement des noms de classes
        if CLASS_NAMES_PATH.exists():
            with open(CLASS_NAMES_PATH, "r") as f:
                self.class_names = json.load(f)
            logger.info("Classes : %s", self.class_names)
        else:
            logger.warning("class_names.json introuvable — fallback : %s", self.class_names)

        num_classes = len(self.class_names)

        # Vérification du fichier modèle
        if not MODEL_PATH.exists():
            logger.error("❌ Modèle introuvable : %s", MODEL_PATH)
            logger.warning("⚠️ MODE SAFE ACTIVÉ — lance d'abord l'entraînement")
            self.is_loaded = True
            return

        try:
            self.model = build_model(num_classes)

            checkpoint = torch.load(MODEL_PATH, map_location=self.device)

            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                state = checkpoint["model_state_dict"]
            elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                state = checkpoint["state_dict"]
            else:
                state = checkpoint

            self.model.load_state_dict(state)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("✅ Modèle chargé avec succès")

        except Exception as e:
            logger.error("❌ Erreur chargement : %s", str(e))
            logger.warning("⚠️ MODE SAFE ACTIVÉ (fallback)")
            self.model     = None
            self.is_loaded = True

    # ── PREDICT ───────────────────────────────────────────────────────────────
    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        if not self.is_loaded:
            raise RuntimeError("Modèle non chargé — appelez load() d'abord")

        # Fallback si modèle absent
        if self.model is None:
            return {
                "class":         "Unknown",
                "confidence":    0.0,
                "probabilities": {c: round(1 / len(self.class_names), 4)
                                  for c in self.class_names},
            }

        # Inférence
        tensor = TRANSFORMS(image).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs  = torch.softmax(logits, dim=1).squeeze(0)

        pred_idx   = int(probs.argmax())
        pred_class = self.class_names[pred_idx]
        confidence = float(probs[pred_idx])

        return {
            "class":      pred_class,
            "confidence": round(confidence, 4),
            "probabilities": {
                name: round(float(probs[i]), 4)
                for i, name in enumerate(self.class_names)
            },
        }