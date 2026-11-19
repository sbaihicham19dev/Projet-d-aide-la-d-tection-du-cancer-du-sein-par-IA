"""
sizer.py
---------
Calcule la taille réelle de la tumeur en centimètres.

Méthode :
    1. Décode le masque base64 PNG
    2. Calcule la bounding box de la zone tumorale
    3. Convertit pixels → cm via PixelSpacing DICOM
    4. Calcule surface, diamètre, périmètre

PixelSpacing standard mammographie :
    - Haute résolution : 0.05 mm/px  (50 µm)
    - Résolution standard : 0.1 mm/px (100 µm)
    - Par défaut : 0.07 mm/px (70 µm) — CBIS-DDSM

Classification taille tumeur (TNM) :
    T1a : < 0.5 cm
    T1b : 0.5 - 1.0 cm
    T1c : 1.0 - 2.0 cm
    T2   : 2.0 - 5.0 cm
    T3   : > 5.0 cm
"""

import base64
import io
import logging
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("tumorsize.sizer")

# PixelSpacing par défaut (mm/pixel) pour mammographie CBIS-DDSM
DEFAULT_PIXEL_SPACING_MM = 0.07   # 70 µm — typique mammographie numérique
IMG_SIZE                 = 224    # taille image U-Net


@dataclass
class TumorSizeResult:
    # Dimensions en pixels
    width_px:    int
    height_px:   int
    area_px:     int
    area_pct:    float

    # Dimensions en cm
    width_cm:    float
    height_cm:   float
    diameter_cm: float   # diamètre moyen
    area_cm2:    float   # surface en cm²

    # Classification TNM
    tnm_stage:   str     # "T1a", "T1b", "T1c", "T2", "T3"
    tnm_desc:    str

    # PixelSpacing utilisé
    pixel_spacing_mm: float
    original_size_px: int   # taille originale de l'image (si connue)


def classify_tnm(diameter_cm: float) -> tuple[str, str]:
    """Classification TNM basée sur le diamètre tumoral."""
    if diameter_cm < 0.5:
        return "T1a", "Micro-tumeur < 0.5 cm"
    elif diameter_cm < 1.0:
        return "T1b", "Petite tumeur 0.5-1.0 cm"
    elif diameter_cm < 2.0:
        return "T1c", "Tumeur 1.0-2.0 cm"
    elif diameter_cm < 5.0:
        return "T2",  "Tumeur 2.0-5.0 cm"
    else:
        return "T3",  "Grande tumeur > 5.0 cm"


class Sizer:
    def __init__(self):
        self.is_loaded = True

    def load(self):
        logger.info("✅ Sizer prêt — conversion px → cm")

    def calculate_from_mask(
        self,
        mask_base64:      str,
        pixel_spacing_mm: float = DEFAULT_PIXEL_SPACING_MM,
        original_size_px: int   = 224,
    ) -> TumorSizeResult:
        """
        Calcule la taille de la tumeur depuis le masque base64.

        pixel_spacing_mm : espacement entre pixels en mm (depuis DICOM)
        original_size_px : taille originale de l'image avant resize
        """
        # Décode le masque
        mask_bytes = base64.b64decode(mask_base64)
        mask       = Image.open(io.BytesIO(mask_bytes)).convert("L")
        mask_np    = np.array(mask)
        h, w       = mask_np.shape

        tumor_pixels = mask_np > 127
        area_px      = int(tumor_pixels.sum())
        area_pct     = round(area_px / (h * w) * 100, 2)

        # Pas de tumeur
        if area_px < (h * w) * 0.005:
            return TumorSizeResult(
                width_px=0, height_px=0, area_px=0, area_pct=0.0,
                width_cm=0.0, height_cm=0.0, diameter_cm=0.0, area_cm2=0.0,
                tnm_stage="T0", tnm_desc="Pas de tumeur détectée",
                pixel_spacing_mm=pixel_spacing_mm,
                original_size_px=original_size_px,
            )

        # Bounding box
        rows, cols = np.where(tumor_pixels)
        rmin, rmax = int(rows.min()), int(rows.max())
        cmin, cmax = int(cols.min()), int(cols.max())

        width_px  = cmax - cmin + 1
        height_px = rmax - rmin + 1

        # Facteur d'échelle : image resizée à 224px depuis original_size_px
        scale_factor = original_size_px / IMG_SIZE

        # Conversion pixels → mm → cm
        # pixel_spacing_mm est pour l'image originale
        # On applique le facteur d'échelle
        effective_spacing_mm = pixel_spacing_mm * scale_factor

        width_mm  = width_px  * effective_spacing_mm
        height_mm = height_px * effective_spacing_mm
        area_mm2  = area_px   * (effective_spacing_mm ** 2)

        width_cm    = round(width_mm  / 10, 2)
        height_cm   = round(height_mm / 10, 2)
        area_cm2    = round(area_mm2  / 100, 3)
        diameter_cm = round((width_cm + height_cm) / 2, 2)

        tnm_stage, tnm_desc = classify_tnm(diameter_cm)

        logger.info(
            "Taille tumeur : %dx%d px → %.1fx%.1f mm → diam=%.2f cm (%s)",
            width_px, height_px, width_mm, height_mm, diameter_cm, tnm_stage
        )

        return TumorSizeResult(
            width_px         = width_px,
            height_px        = height_px,
            area_px          = area_px,
            area_pct         = area_pct,
            width_cm         = width_cm,
            height_cm        = height_cm,
            diameter_cm      = diameter_cm,
            area_cm2         = area_cm2,
            tnm_stage        = tnm_stage,
            tnm_desc         = tnm_desc,
            pixel_spacing_mm = pixel_spacing_mm,
            original_size_px = original_size_px,
        )

    def calculate_from_area_pct(
        self,
        tumor_area_pct:   float,
        pixel_spacing_mm: float = DEFAULT_PIXEL_SPACING_MM,
        original_size_px: int   = 224,
    ) -> TumorSizeResult:
        """
        Calcule la taille estimée depuis le pourcentage de surface.
        Utilisé quand le masque n'est pas disponible.
        """
        total_px  = IMG_SIZE * IMG_SIZE
        area_px   = int(total_px * tumor_area_pct / 100)

        # Estimation bounding box (tumeur ~ circulaire)
        radius_px = math.sqrt(area_px / math.pi)
        bbox_px   = int(radius_px * 2)

        scale_factor         = original_size_px / IMG_SIZE
        effective_spacing_mm = pixel_spacing_mm * scale_factor

        diameter_mm = bbox_px * effective_spacing_mm
        diameter_cm = round(diameter_mm / 10, 2)
        area_cm2    = round(area_px * (effective_spacing_mm ** 2) / 100, 3)

        tnm_stage, tnm_desc = classify_tnm(diameter_cm)

        return TumorSizeResult(
            width_px         = bbox_px,
            height_px        = bbox_px,
            area_px          = area_px,
            area_pct         = tumor_area_pct,
            width_cm         = diameter_cm,
            height_cm        = diameter_cm,
            diameter_cm      = diameter_cm,
            area_cm2         = area_cm2,
            tnm_stage        = tnm_stage,
            tnm_desc         = tnm_desc,
            pixel_spacing_mm = pixel_spacing_mm,
            original_size_px = original_size_px,
        )