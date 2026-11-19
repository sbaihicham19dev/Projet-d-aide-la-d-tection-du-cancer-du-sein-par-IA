"""
Tumor size estimation from a segmentation mask.

For this pipeline the segmentation mask is produced at 224x224 from JPG images.
Without true DICOM PixelSpacing, scaling the mask back to the original JPG size
can create impossible diameters. The default calculation therefore measures in
the model space with a conservative CBIS-DDSM calibration.
"""

import base64
import io
import logging
import math
from dataclasses import dataclass

import numpy as np
from PIL import Image

logger = logging.getLogger("tumorsize.sizer")

DEFAULT_PIXEL_SPACING_MM = 0.07
IMG_SIZE = 224
MIN_TUMOR_AREA_PCT = 0.5
ABERRANT_MASK_PCT = 40.0


@dataclass
class TumorSizeResult:
    width_px: int
    height_px: int
    area_px: int
    area_pct: float
    width_cm: float
    height_cm: float
    diameter_cm: float
    area_cm2: float
    tnm_stage: str
    tnm_desc: str
    pixel_spacing_mm: float
    original_size_px: int


def classify_tnm(diameter_cm: float) -> tuple[str, str]:
    if diameter_cm <= 0:
        return "T0", "Pas de tumeur detectee"
    if diameter_cm < 0.5:
        return "T1a", "Micro-tumeur < 0.5 cm"
    if diameter_cm < 1.0:
        return "T1b", "Petite tumeur 0.5-1.0 cm"
    if diameter_cm < 2.0:
        return "T1c", "Tumeur 1.0-2.0 cm"
    if diameter_cm < 5.0:
        return "T2", "Tumeur 2.0-5.0 cm"
    return "T3", "Grande tumeur > 5.0 cm"


def _empty_result(pixel_spacing_mm: float, original_size_px: int) -> TumorSizeResult:
    return TumorSizeResult(
        width_px=0,
        height_px=0,
        area_px=0,
        area_pct=0.0,
        width_cm=0.0,
        height_cm=0.0,
        diameter_cm=0.0,
        area_cm2=0.0,
        tnm_stage="T0",
        tnm_desc="Pas de tumeur detectee",
        pixel_spacing_mm=pixel_spacing_mm,
        original_size_px=original_size_px,
    )


class Sizer:
    def __init__(self):
        self.is_loaded = True

    def load(self):
        logger.info("Sizer pret - conversion px vers cm")

    def calculate_from_mask(
        self,
        mask_base64: str,
        pixel_spacing_mm: float = DEFAULT_PIXEL_SPACING_MM,
        original_size_px: int = IMG_SIZE,
    ) -> TumorSizeResult:
        mask_bytes = base64.b64decode(mask_base64)
        mask = Image.open(io.BytesIO(mask_bytes)).convert("L")
        mask_np = np.array(mask)
        h, w = mask_np.shape

        tumor_pixels = mask_np > 127
        area_px = int(tumor_pixels.sum())
        area_pct = round(area_px / (h * w) * 100, 2)

        if area_pct < MIN_TUMOR_AREA_PCT:
            return _empty_result(pixel_spacing_mm, original_size_px)

        rows, cols = np.where(tumor_pixels)
        width_px = int(cols.max() - cols.min() + 1)
        height_px = int(rows.max() - rows.min() + 1)

        if area_pct > ABERRANT_MASK_PCT:
            # Large masks often include breast tissue, not only the lesion.
            # A circular-equivalent diameter is less explosive than full bbox.
            diameter_px = int(math.sqrt(area_px / math.pi) * 2)
            measured_width_px = diameter_px
            measured_height_px = diameter_px
        else:
            measured_width_px = width_px
            measured_height_px = height_px

        width_mm = measured_width_px * pixel_spacing_mm
        height_mm = measured_height_px * pixel_spacing_mm
        area_mm2 = area_px * (pixel_spacing_mm ** 2)

        width_cm = round(width_mm / 10, 2)
        height_cm = round(height_mm / 10, 2)
        area_cm2 = round(area_mm2 / 100, 3)
        diameter_cm = round(max(width_cm, height_cm), 2)
        tnm_stage, tnm_desc = classify_tnm(diameter_cm)

        logger.info(
            "Taille tumeur : %dx%d px, area=%.2f%% -> diam=%.2f cm (%s)",
            measured_width_px,
            measured_height_px,
            area_pct,
            diameter_cm,
            tnm_stage,
        )

        return TumorSizeResult(
            width_px=measured_width_px,
            height_px=measured_height_px,
            area_px=area_px,
            area_pct=area_pct,
            width_cm=width_cm,
            height_cm=height_cm,
            diameter_cm=diameter_cm,
            area_cm2=area_cm2,
            tnm_stage=tnm_stage,
            tnm_desc=tnm_desc,
            pixel_spacing_mm=pixel_spacing_mm,
            original_size_px=original_size_px,
        )

    def calculate_from_area_pct(
        self,
        tumor_area_pct: float,
        pixel_spacing_mm: float = DEFAULT_PIXEL_SPACING_MM,
        original_size_px: int = IMG_SIZE,
    ) -> TumorSizeResult:
        total_px = IMG_SIZE * IMG_SIZE
        area_px = int(total_px * tumor_area_pct / 100)

        if tumor_area_pct < MIN_TUMOR_AREA_PCT:
            return _empty_result(pixel_spacing_mm, original_size_px)

        radius_px = math.sqrt(area_px / math.pi)
        bbox_px = int(radius_px * 2)

        diameter_mm = bbox_px * pixel_spacing_mm
        diameter_cm = round(diameter_mm / 10, 2)
        area_cm2 = round(area_px * (pixel_spacing_mm ** 2) / 100, 3)
        tnm_stage, tnm_desc = classify_tnm(diameter_cm)

        return TumorSizeResult(
            width_px=bbox_px,
            height_px=bbox_px,
            area_px=area_px,
            area_pct=tumor_area_pct,
            width_cm=diameter_cm,
            height_cm=diameter_cm,
            diameter_cm=diameter_cm,
            area_cm2=area_cm2,
            tnm_stage=tnm_stage,
            tnm_desc=tnm_desc,
            pixel_spacing_mm=pixel_spacing_mm,
            original_size_px=original_size_px,
        )
