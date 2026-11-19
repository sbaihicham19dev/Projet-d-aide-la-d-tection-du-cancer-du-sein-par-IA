"""
Segmentor — U-Net pour segmentation de tumeur mammaire
Entrée  : image PIL
Sortie  : masque binaire PNG (blanc = tumeur, noir = fond)
"""
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
import numpy as np

logger = logging.getLogger("segmentation.segmentor")

BASE_DIR   = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "unet_224.pt"

IMG_SIZE = 224

# ── Transform ─────────────────────────────────────────────────────────────────
TRANSFORM = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.Grayscale(num_output_channels=1),
    T.ToTensor(),
    T.Normalize(mean=[0.5], std=[0.5]),
])


# ── U-Net Architecture ────────────────────────────────────────────────────────
class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, features=[64, 128, 256, 512]):
        super().__init__()
        self.downs     = nn.ModuleList()
        self.ups       = nn.ModuleList()
        self.pool      = nn.MaxPool2d(2, 2)

        # Encoder
        for f in features:
            self.downs.append(DoubleConv(in_channels, f))
            in_channels = f

        # Bottleneck
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        # Decoder
        for f in reversed(features):
            self.ups.append(nn.ConvTranspose2d(f * 2, f, 2, 2))
            self.ups.append(DoubleConv(f * 2, f))

        # Output
        self.final = nn.Conv2d(features[0], out_channels, 1)

    def forward(self, x):
        skip_connections = []

        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]

        for i in range(0, len(self.ups), 2):
            x    = self.ups[i](x)
            skip = skip_connections[i // 2]

            if x.shape != skip.shape:
                x = torch.nn.functional.interpolate(x, size=skip.shape[2:])

            x = torch.cat([skip, x], dim=1)
            x = self.ups[i + 1](x)

        return self.final(x)


# ── Segmentor class ───────────────────────────────────────────────────────────
class Segmentor:
    def __init__(self):
        self.model     = None
        self.device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False

    def load(self) -> None:
        logger.info("Chargement U-Net depuis %s …", MODEL_PATH)

        self.model = UNet(in_channels=1, out_channels=1)

        if not MODEL_PATH.exists():
            logger.warning("⚠️ unet_224.pt introuvable — mode fallback activé")
            self.is_loaded = True
            return

        try:
            state = torch.load(MODEL_PATH, map_location=self.device)
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            self.model.load_state_dict(state)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("✅ U-Net chargé avec succès")
        except Exception as e:
            logger.error("❌ Erreur chargement U-Net : %s", e)
            self.model     = None
            self.is_loaded = True

    @torch.no_grad()
    def segment(self, image: Image.Image) -> dict:
        """
        Retourne :
            mask_image    : Image PIL binaire (L mode)
            tumor_area_px : pixels blancs
            tumor_area_pct: pourcentage
        """
        if not self.is_loaded:
            raise RuntimeError("Modèle non chargé")

        # Fallback : masque vide si modèle absent
        if self.model is None:
            empty = Image.new("L", (IMG_SIZE, IMG_SIZE), 0)
            return {
                "mask_image":     empty,
                "tumor_area_px":  0,
                "tumor_area_pct": 0.0,
            }

        # Prétraitement
        tensor = TRANSFORM(image).unsqueeze(0).to(self.device)

        # Inférence
        logits = self.model(tensor)
        probs  = torch.sigmoid(logits).squeeze().cpu().numpy()

        # Seuillage binaire
        mask_np = (probs > 0.5).astype(np.uint8) * 255
        mask_img = Image.fromarray(mask_np, mode="L").resize(
            (IMG_SIZE, IMG_SIZE), Image.NEAREST
        )

        # Calcul surface tumeur
        total_px      = IMG_SIZE * IMG_SIZE
        tumor_area_px = int(np.sum(mask_np > 0))
        tumor_area_pct = round(tumor_area_px / total_px * 100, 2)

        return {
            "mask_image":     mask_img,
            "tumor_area_px":  tumor_area_px,
            "tumor_area_pct": tumor_area_pct,
        }