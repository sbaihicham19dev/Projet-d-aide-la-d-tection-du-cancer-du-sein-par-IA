"""
predictor.py
Charge le modele ResNet50 et fait la prediction.
Supporte JPEG, PNG et DICOM (.dcm)
"""

import os
import cv2
import json
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config depuis .env ────────────────────────────────────
MODEL_PATH       = Path(os.getenv("MODEL_PATH",       "models/resnet50_mammography.pt"))
CLASS_NAMES_PATH = Path(os.getenv("CLASS_NAMES_PATH", "models/class_names.json"))
IMAGE_SIZE       = int(os.getenv("IMAGE_SIZE",        224))
DEVICE           = torch.device(os.getenv("DEVICE",   "cpu"))

# ── Transform ─────────────────────────────────────────────
TRANSFORM = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


def build_model(num_classes: int = 2) -> nn.Module:
    """Reconstruit l'architecture ResNet50 identique au training."""
    model = models.resnet50(weights=None)
    in_features = model.fc.in_features  # 2048
    model.fc = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(in_features, num_classes)
    )
    return model


class Predictor:
    def __init__(self):
        with open(CLASS_NAMES_PATH, "r") as f:
            self.class_names = json.load(f)

        self.model = build_model(num_classes=len(self.class_names))
        self.model.load_state_dict(
            torch.load(MODEL_PATH, map_location=DEVICE)
        )
        self.model.to(DEVICE)
        self.model.eval()
        print(f"[INFO] Modele charge sur {DEVICE}")
        print(f"[INFO] Classes : {self.class_names}")

    def _load_image(self, file_bytes: bytes, filename: str) -> np.ndarray:
        ext = Path(filename).suffix.lower()

        if ext == ".dcm":
            try:
                import pydicom
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                ds  = pydicom.dcmread(tmp_path)
                img = ds.pixel_array.astype(np.float32)
                img = ((img - img.min()) / (img.max() - img.min() + 1e-8) * 255).astype(np.uint8)
                os.unlink(tmp_path)
            except ImportError:
                raise ValueError("pydicom requis. pip install pydicom")
        else:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img   = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            raise ValueError("Impossible de lire l'image.")

        # Preprocessing identique au training
        coords = cv2.findNonZero(img)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            img = img[y:y+h, x:x+w]

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img   = clahe.apply(img)
        img   = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        return img

    def predict(self, file_bytes: bytes, filename: str) -> dict:
        img    = self._load_image(file_bytes, filename)
        tensor = TRANSFORM(img).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = self.model(tensor)
            probs   = torch.softmax(outputs, dim=1)[0]

        probs_dict = {
            self.class_names[str(i)]: round(probs[i].item(), 4)
            for i in range(len(self.class_names))
        }

        # Seuil abaisse pour Cancer (reduire les faux negatifs)
        # Index 0 = Cancer, Index 1 = Non-Cancer
        CANCER_THRESHOLD = 0.3
        cancer_prob = probs[0].item()

        if cancer_prob >= CANCER_THRESHOLD:
            label      = self.class_names["0"]   # Cancer
            confidence = round(cancer_prob, 4)
        else:
            label      = self.class_names["1"]   # Non-Cancer
            confidence = round(probs[1].item(), 4)

        return {
            "label":         label,
            "confidence":    confidence,
            "probabilities": probs_dict,
        }


predictor = Predictor()