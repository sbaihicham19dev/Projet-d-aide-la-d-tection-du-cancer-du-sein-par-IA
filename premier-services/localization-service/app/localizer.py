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
"""

import base64
import io
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("localization.localizer")

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
    quadrant:        str
    quadrant_name:   str
    quadrant_fr:     str
    centroid_x:      float
    centroid_y:      float
    centroid_x_px:   int
    centroid_y_px:   int
    tumor_area_pct:  float
    confidence:      float


class Localizer:
    def __init__(self):
        self.is_loaded = True
        logger.info("✅ Localizer initialisé")

    def load(self):
        logger.info("✅ Localizer prêt — pas de modèle requis")

    def localize_from_mask(
        self,
        mask_base64: str,
        side: Optional[str] = None,
    ) -> LocalizationResult:
        try:
            # Décode le masque — supporte L, RGB, RGBA
            mask_bytes = base64.b64decode(mask_base64)
            mask_img   = Image.open(io.BytesIO(mask_bytes))

            # Convertit en niveaux de gris peu importe le mode source
            if mask_img.mode == "RGBA":
                # Canal alpha comme masque
                mask_np = np.array(mask_img)[:, :, 3]
            elif mask_img.mode == "RGB":
                mask_np = np.array(mask_img.convert("L"))
            else:
                mask_np = np.array(mask_img.convert("L"))

            h, w = mask_np.shape

            # FIX: seuil adaptatif — utilise la médiane si le masque est binaire
            max_val = mask_np.max()
            if max_val == 0:
                threshold = 1
            elif max_val <= 1:
                # Masque binaire 0/1
                threshold = 0
            else:
                # Masque 0-255 — seuil à 10% du max (au lieu de 127)
                threshold = max(10, max_val * 0.1)

            tumor_pixels = mask_np > threshold
            tumor_count  = int(tumor_pixels.sum())
            total_pixels = h * w
            tumor_pct    = round(tumor_count / total_pixels * 100, 2)

            logger.info(
                "Masque décodé — taille=%dx%d  max=%d  threshold=%.1f  "
                "tumor_px=%d  tumor_pct=%.2f%%",
                w, h, max_val, threshold, tumor_count, tumor_pct,
            )

            # FIX: seuil abaissé à 0.1% (au lieu de 1%)
            if tumor_count < total_pixels * 0.001:
                logger.warning("Tumeur trop petite ou masque vide — fallback image")
                return self._no_tumor_result(w, h)

            # Centroïde
            rows, cols = np.where(tumor_pixels)
            centroid_y = float(rows.mean())
            centroid_x = float(cols.mean())
            cx_norm    = centroid_x / w
            cy_norm    = centroid_y / h

            quadrant   = self._get_quadrant(cx_norm, cy_norm)

            # Confiance
            std_x      = float(cols.std()) / w if len(cols) > 1 else 0.5
            std_y      = float(rows.std()) / h if len(rows) > 1 else 0.5
            spread     = (std_x + std_y) / 2
            confidence = round(max(0.3, min(0.99, 1.0 - spread * 2)), 3)

            logger.info(
                "Localisation — centroïde=(%.3f, %.3f)  quadrant=%s  conf=%.3f",
                cx_norm, cy_norm, quadrant, confidence,
            )

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
            logger.error("❌ Erreur localisation depuis masque : %s", e, exc_info=True)
            return self._no_tumor_result(224, 224)

    def _get_quadrant(self, cx: float, cy: float) -> str:
        """
        Détermine le quadrant depuis le centroïde normalisé (0-1).

        Zone centrale élargie à ±20% pour les tumeurs rétro-aréolaires
        qui sont fréquentes dans CBIS-DDSM.
        """
        # Zone centrale (±20% du centre)
        if abs(cx - 0.5) < 0.20 and abs(cy - 0.5) < 0.20:
            return "C"

        # Quadrants
        if cy < 0.5:      # Haut (Upper)
            return "UO" if cx > 0.5 else "UI"
        else:             # Bas (Lower)
            return "LO" if cx > 0.5 else "LI"

    def _no_tumor_result(self, w: int, h: int) -> LocalizationResult:
        return LocalizationResult(
            quadrant       = "N",
            quadrant_name  = QUADRANTS["N"],
            quadrant_fr    = QUADRANTS_FR["N"],
            centroid_x     = 0.5,
            centroid_y     = 0.5,
            centroid_x_px  = w // 2,
            centroid_y_px  = h // 2,
            tumor_area_pct = 0.0,
            confidence     = 0.0,
        )

    def localize_from_image(self, image: Image.Image) -> LocalizationResult:
        """
        Localise directement depuis une image sans masque.
        Utilise le seuillage pour détecter la zone dense (tumeur potentielle).
        """
        gray   = image.convert("L").resize((224, 224))
        img_np = np.array(gray)

        # Seuil adaptatif — zone plus dense que moyenne + 0.5 écart-type
        threshold = img_np.mean() + img_np.std() * 0.5
        dense     = img_np > threshold
        count     = int(dense.sum())

        if count < 224 * 224 * 0.005:  # FIX: 0.5% au lieu de 2%
            return self._no_tumor_result(224, 224)

        rows, cols = np.where(dense)
        cx = float(cols.mean()) / 224
        cy = float(rows.mean()) / 224
        quadrant = self._get_quadrant(cx, cy)

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