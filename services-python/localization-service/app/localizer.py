"""
localizer.py
-------------
Localise la tumeur dans le sein depuis le masque de segmentation.

Quadrants :
    UO → Upper Outer  (Haut Externe)   — quadrant le plus fréquent
    UI → Upper Inner  (Haut Interne)
    LO → Lower Outer  (Bas Externe)
    LI → Lower Inner  (Bas Interne)
    C  → Central      (Zone centrale)
    N  → No tumor     (Pas de tumeur)

Méthode :
    1. Décode le masque base64 PNG
    2. Calcule le centroïde de la zone tumorale
    3. Détermine le quadrant selon la position du centroïde
    4. Calcule les coordonnées normalisées (0-1)
"""

import base64
import io
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("localization.localizer")

# ── Quadrant mapping ──────────────────────────────────────────────────────────
QUADRANTS = {
    "UO": "Upper Outer (Haut Externe)",
    "UI": "Upper Inner (Haut Interne)",
    "LO": "Lower Outer (Bas Externe)",
    "LI": "Lower Inner (Bas Interne)",
    "C":  "Central (Zone centrale)",
    "N":  "No tumor detected",
}

QUADRANTS_FR = {
    "UO": "Quadrant supéro-externe",
    "UI": "Quadrant supéro-interne",
    "LO": "Quadrant inféro-externe",
    "LI": "Quadrant inféro-interne",
    "C":  "Zone centrale / rétro-aréolaire",
    "N":  "Pas de tumeur détectée",
}


@dataclass
class LocalizationResult:
    quadrant:        str    # "UO", "UI", "LO", "LI", "C", "N"
    quadrant_name:   str    # nom complet
    quadrant_fr:     str    # nom en français
    centroid_x:      float  # position X normalisée (0-1)
    centroid_y:      float  # position Y normalisée (0-1)
    centroid_x_px:   int    # position X en pixels
    centroid_y_px:   int    # position Y en pixels
    tumor_area_pct:  float  # % surface tumorale
    confidence:      float  # confiance de la localisation


class Localizer:
    def __init__(self):
        self.is_loaded = True
        logger.info("✅ Localizer initialisé")

    def load(self):
        logger.info("✅ Localizer prêt — pas de modèle requis")

    def localize_from_mask(
        self,
        mask_base64: str,
        side: Optional[str] = None,  # "LEFT" ou "RIGHT" (optionnel)
    ) -> LocalizationResult:
        """
        Localise la tumeur depuis le masque base64.
        """
        try:
            # Décode le masque
            mask_bytes = base64.b64decode(mask_base64)
            mask       = Image.open(io.BytesIO(mask_bytes)).convert("L")
            mask_np    = np.array(mask)
            h, w       = mask_np.shape

            # Pixels tumoraux
            tumor_pixels = mask_np > 127
            tumor_count  = tumor_pixels.sum()
            total_pixels = h * w
            tumor_pct    = round(tumor_count / total_pixels * 100, 2)

            # Pas de tumeur
            if tumor_count < total_pixels * 0.01:
                return LocalizationResult(
                    quadrant       = "N",
                    quadrant_name  = QUADRANTS["N"],
                    quadrant_fr    = QUADRANTS_FR["N"],
                    centroid_x     = 0.5,
                    centroid_y     = 0.5,
                    centroid_x_px  = w // 2,
                    centroid_y_px  = h // 2,
                    tumor_area_pct = tumor_pct,
                    confidence     = 0.0,
                )

            # Calcule le centroïde
            rows, cols   = np.where(tumor_pixels)
            centroid_y   = float(rows.mean())
            centroid_x   = float(cols.mean())

            # Normalise (0-1)
            cx_norm = centroid_x / w
            cy_norm = centroid_y / h

            # Détermine le quadrant
            quadrant = self._get_quadrant(cx_norm, cy_norm, w, h, mask_np)

            # Confiance basée sur la concentration de pixels
            std_x = float(cols.std()) / w
            std_y = float(rows.std()) / h
            spread = (std_x + std_y) / 2
            confidence = round(max(0.3, 1.0 - spread * 2), 3)

            return LocalizationResult(
                quadrant       = quadrant,
                quadrant_name  = QUADRANTS[quadrant],
                quadrant_fr    = QUADRANTS_FR[quadrant],
                centroid_x     = round(cx_norm, 4),
                centroid_y     = round(cy_norm, 4),
                centroid_x_px  = int(centroid_x),
                centroid_y_px  = int(centroid_y),
                tumor_area_pct = tumor_pct,
                confidence     = confidence,
            )

        except Exception as e:
            logger.error("❌ Erreur localisation : %s", e)
            return LocalizationResult(
                quadrant       = "N",
                quadrant_name  = QUADRANTS["N"],
                quadrant_fr    = QUADRANTS_FR["N"],
                centroid_x     = 0.5,
                centroid_y     = 0.5,
                centroid_x_px  = 112,
                centroid_y_px  = 112,
                tumor_area_pct = 0.0,
                confidence     = 0.0,
            )

    def _get_quadrant(
        self, cx: float, cy: float,
        w: int, h: int, mask_np: np.ndarray
    ) -> str:
        """Détermine le quadrant depuis le centroïde normalisé."""

        # Zone centrale (±15% du centre)
        if abs(cx - 0.5) < 0.15 and abs(cy - 0.5) < 0.15:
            return "C"

        # Quadrants
        if cy < 0.5:  # Haut (Upper)
            if cx > 0.5:
                return "UO"  # Haut Externe (droite de l'image)
            else:
                return "UI"  # Haut Interne (gauche de l'image)
        else:          # Bas (Lower)
            if cx > 0.5:
                return "LO"  # Bas Externe
            else:
                return "LI"  # Bas Interne

    def localize_from_image(self, image: Image.Image) -> LocalizationResult:
        """
        Localise directement depuis une image sans masque.
        Utilise le seuillage pour détecter la zone dense (tumeur potentielle).
        """
        gray   = image.convert("L").resize((224, 224))
        img_np = np.array(gray)

        # Seuil adaptatif — zone plus dense que la moyenne
        threshold = img_np.mean() + img_np.std() * 0.5
        dense     = img_np > threshold
        count     = dense.sum()

        if count < 224 * 224 * 0.02:
            return LocalizationResult(
                quadrant="N", quadrant_name=QUADRANTS["N"],
                quadrant_fr=QUADRANTS_FR["N"],
                centroid_x=0.5, centroid_y=0.5,
                centroid_x_px=112, centroid_y_px=112,
                tumor_area_pct=0.0, confidence=0.0,
            )

        rows, cols = np.where(dense)
        cx = float(cols.mean()) / 224
        cy = float(rows.mean()) / 224
        quadrant = self._get_quadrant(cx, cy, 224, 224, dense.astype(np.uint8) * 255)

        return LocalizationResult(
            quadrant       = quadrant,
            quadrant_name  = QUADRANTS[quadrant],
            quadrant_fr    = QUADRANTS_FR[quadrant],
            centroid_x     = round(cx, 4),
            centroid_y     = round(cy, 4),
            centroid_x_px  = int(cols.mean()),
            centroid_y_px  = int(rows.mean()),
            tumor_area_pct = round(count / (224 * 224) * 100, 2),
            confidence     = 0.6,
        )