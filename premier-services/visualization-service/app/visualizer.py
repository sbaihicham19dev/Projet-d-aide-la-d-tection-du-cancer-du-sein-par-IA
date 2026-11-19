import base64
import io
import math
from collections import deque
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class GradCamVisualizer:

    MAX_LESION_AREA_PCT = 40.0
    MIN_LESION_AREA_PCT = 0.02
    ABERRANT_MASK_PCT   = 50.0

    def visualize(
        self,
        image: Image.Image,
        mask_base64: Optional[str] = None,
        tumor_area_pct: Optional[float] = None,
        include_images: bool = True,
    ) -> dict:
        image = image.convert("RGB")
        work_image = image.copy()
        work_image.thumbnail((768, 768))
        gray = np.asarray(work_image.convert("L")).astype("float32") / 255.0
        breast = self._breast_mask(gray)

        heat = None
        method = "density-guided-gradcam"
        quality_warning = None

        if mask_base64:
            mask_heat, mask_area_pct = self._heat_from_mask(work_image, mask_base64)

            if mask_area_pct <= self.MAX_LESION_AREA_PCT:
                heat = self._refine_heat(mask_heat, gray, breast)
                method = "mask-guided-gradcam"

            elif mask_area_pct <= self.ABERRANT_MASK_PCT:
                quality_warning = (
                    f"Masque de segmentation large ({mask_area_pct:.2f}%). "
                    "Visualisation par analyse d'intensité."
                )
                method = "intensity-gradcam-fallback"
                heat = self._heat_from_intensity(gray, breast)

            else:
                quality_warning = (
                    f"Masque de segmentation aberrant ({mask_area_pct:.2f}%). "
                    "Visualisation recentrée sur les zones denses compactes."
                )
                method = "density-guided-gradcam-fallback"

        if heat is None:
            heat = self._heat_from_density(gray, breast)
            if method == "density-guided-gradcam":
                quality_warning = "Aucun masque exploitable; visualisation basée sur les zones denses compactes."

        heat = self._resize_heat(heat, image.size)

        bbox = self._lesion_bbox(heat)
        focus_score = self._focus_score(heat, bbox)
        estimated_area_pct = round(float((heat > 0.55).mean() * 100), 4)
        if tumor_area_pct is None or tumor_area_pct > self.ABERRANT_MASK_PCT:
            tumor_area_pct = estimated_area_pct

        result = {
            "method": method,
            "quality_warning": quality_warning,
            "focus_score": focus_score,
            "tumor_area_pct": tumor_area_pct,
            "width": image.width,
            "height": image.height,
            "lesion_bbox": bbox,
        }

        if include_images:
            overlay = self._overlay(image, heat, bbox)
            result["overlay_base64"] = self._png_base64(overlay)
            result["heatmap_base64"] = self._png_base64(self._colorize(heat))
            lesion = self._lesion_crop(overlay, bbox)
            if lesion is not None:
                result["lesion_base64"] = self._png_base64(lesion)

        return result

    # ── Mask & heat sources ──────────────────────────────────────────────

    def _mask_is_plausible(self, area_pct: float) -> bool:
        return self.MIN_LESION_AREA_PCT <= area_pct <= self.MAX_LESION_AREA_PCT

    def _heat_from_mask(self, image: Image.Image, mask_base64: str) -> tuple[np.ndarray, float]:
        raw = base64.b64decode(mask_base64)
        mask = Image.open(io.BytesIO(raw)).convert("L").resize(image.size)
        arr = np.asarray(mask).astype("float32") / 255.0
        area_pct = float((arr > 0.5).mean() * 100)
        arr = self._largest_component(arr > 0.5).astype("float32")
        arr = self._blur(arr, image.size)
        return self._normalize(arr), area_pct

    def _heat_from_density(self, gray: np.ndarray, breast: np.ndarray) -> np.ndarray:
        if not breast.any():
            return self._normalize(gray)
        values = gray[breast]
        dense_threshold = max(
            float(np.quantile(values, 0.88)),
            float(values.mean() + values.std() * 0.65)
        )
        candidates = (gray >= dense_threshold) & breast
        candidates = self._remove_border_band(candidates)
        component = self._best_dense_component(candidates, gray)
        if not component.any():
            component = candidates
        if not component.any():
            return self._normalize(gray * breast)
        heat = self._blur(component.astype("float32"), (gray.shape[1], gray.shape[0]))
        heat *= np.clip(gray * 1.4, 0, 1)
        return self._normalize(heat)

    def _heat_from_intensity(self, gray: np.ndarray, breast: np.ndarray) -> np.ndarray:
        if not breast.any():
            return self._normalize(gray)
        values = gray[breast]
        intensity_threshold = max(
            float(np.quantile(values, 0.75)),
            float(values.mean() + values.std() * 0.3)
        )
        candidates = (gray >= intensity_threshold) & breast
        candidates = self._remove_border_band(candidates)
        components = self._components(candidates)
        h, w = gray.shape
        image_area = h * w
        combined = np.zeros_like(gray, dtype=bool)
        for comp in components:
            area_pct = float(comp.sum()) / image_area * 100
            if area_pct < self.MIN_LESION_AREA_PCT:
                continue
            if not self._component_is_plausible_region(comp):
                continue
            if float((combined | comp).sum()) / image_area * 100 > self.MAX_LESION_AREA_PCT:
                break
            combined |= comp
        if not combined.any():
            combined = candidates
        heat = self._blur(combined.astype("float32"), (w, h))
        heat *= np.clip(gray * 1.2, 0, 1)
        return self._normalize(heat)

    def _refine_heat(self, mask_heat: np.ndarray, gray: np.ndarray, breast: np.ndarray) -> np.ndarray:
        dense_heat = self._heat_from_density(gray, breast)
        combined = (mask_heat * 0.55) + (dense_heat * 0.45)
        return self._normalize(combined * breast)

    # ── Breast mask & region helpers ─────────────────────────────────────

    def _breast_mask(self, gray: np.ndarray) -> np.ndarray:
        threshold = max(0.04, float(np.quantile(gray, 0.18)))
        mask = gray > threshold
        return self._largest_component(mask)

    def _remove_border_band(self, mask: np.ndarray) -> np.ndarray:
        cleaned = mask.copy()
        h, w = cleaned.shape
        band = max(4, min(w, h) // 70)
        cleaned[:band, :]  = False
        cleaned[-band:, :] = False
        cleaned[:, :band]  = False
        cleaned[:, -band:] = False
        return cleaned

    def _best_dense_component(self, mask: np.ndarray, gray: np.ndarray) -> np.ndarray:
        components = self._components(mask)
        if not components:
            return np.zeros_like(mask, dtype=bool)
        h, w = mask.shape
        image_area = h * w
        best_score = -1.0
        best = np.zeros_like(mask, dtype=bool)
        for comp in components:
            area = int(comp.sum())
            area_pct = area / image_area * 100
            if area_pct < self.MIN_LESION_AREA_PCT or area_pct > self.MAX_LESION_AREA_PCT:
                continue
            if not self._component_is_plausible_region(comp):
                continue
            ys, xs = np.where(comp)
            box_area = max(1, (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1))
            compactness = area / box_area
            intensity = float(gray[comp].mean())
            score = intensity * 0.7 + compactness * 0.3
            if score > best_score:
                best_score = score
                best = comp
        return best

    def _component_is_plausible_region(self, comp: np.ndarray) -> bool:
        ys, xs = np.where(comp)
        if len(xs) == 0 or len(ys) == 0:
            return False
        h, w = comp.shape
        left, right = int(xs.min()), int(xs.max())
        top, bottom = int(ys.min()), int(ys.max())
        box_w = right - left + 1
        box_h = bottom - top + 1
        min_dim = min(w, h)
        border = max(4, int(min_dim * 0.025))
        touches_vertical_border = left <= border or right >= w - border - 1
        very_thin = box_w < max(5, int(min_dim * 0.025)) or box_h < max(5, int(min_dim * 0.025))
        elongated = max(box_w / max(box_h, 1), box_h / max(box_w, 1)) > 7.0
        return not (touches_vertical_border and (very_thin or elongated))

    def _components(self, mask: np.ndarray) -> list[np.ndarray]:
        h, w = mask.shape
        seen = np.zeros_like(mask, dtype=bool)
        comps: list[np.ndarray] = []
        for y, x in zip(*np.where(mask & ~seen)):
            if seen[y, x]:
                continue
            comp = np.zeros_like(mask, dtype=bool)
            queue = deque([(int(y), int(x))])
            seen[y, x] = True
            while queue:
                cy, cx = queue.popleft()
                comp[cy, cx] = True
                for ny in (cy - 1, cy, cy + 1):
                    for nx in (cx - 1, cx, cx + 1):
                        if ny == cy and nx == cx:
                            continue
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
            comps.append(comp)
        comps.sort(key=lambda c: int(c.sum()), reverse=True)
        return comps[:32]

    def _largest_component(self, mask: np.ndarray) -> np.ndarray:
        components = self._components(mask)
        if not components:
            return np.zeros_like(mask, dtype=bool)
        return components[0]

    # ── Image processing ─────────────────────────────────────────────────

    def _blur(self, arr: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        radius = max(4, min(size) // 55)
        image = Image.fromarray((np.clip(arr, 0, 1) * 255).astype("uint8"), mode="L")
        image = image.filter(ImageFilter.GaussianBlur(radius=radius))
        return np.asarray(image).astype("float32") / 255.0

    def _resize_heat(self, heat: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        image = Image.fromarray((np.clip(heat, 0, 1) * 255).astype("uint8"), mode="L")
        image = image.resize(size, Image.Resampling.BILINEAR)
        return np.asarray(image).astype("float32") / 255.0

    def _overlay(self, image: Image.Image, heat: np.ndarray, bbox: Optional[list[int]] = None) -> Image.Image:
        h = np.clip(heat, 0, 1)
        # Fond noir transparent, toute la heatmap visible comme image 2
        alpha = np.where(
            h < 0.15,
            np.zeros_like(h, dtype="uint8"),
            np.clip(h * 220, 0, 210)
        ).astype("uint8")
        heat_img = self._colorize(heat).convert("RGBA")
        heat_img.putalpha(Image.fromarray(alpha))
        base = image.convert("RGBA")
        overlay = Image.alpha_composite(base, heat_img).convert("RGB")
        if bbox:
            draw = ImageDraw.Draw(overlay)
            width = max(5, min(image.size) // 80)
            draw.rectangle(bbox, outline=(255, 24, 24), width=width)
        return overlay

    def _colorize(self, heat: np.ndarray) -> Image.Image:
        h = np.clip(heat, 0, 1) ** 0.72
        stops = np.array(
            [
                [0.00,   0,   0, 255],   # bleu foncé
                [0.20,   0, 150, 255],   # bleu clair
                [0.40,   0, 255, 200],   # cyan
                [0.55,  80, 255,  80],   # vert
                [0.70, 255, 255,   0],   # jaune
                [0.85, 255, 130,   0],   # orange
                [1.00, 255,   0,   0],   # rouge
            ],
            dtype="float32",
        )
        flat = h.reshape(-1)
        r = np.interp(flat, stops[:, 0], stops[:, 1]).reshape(h.shape)
        g = np.interp(flat, stops[:, 0], stops[:, 2]).reshape(h.shape)
        b = np.interp(flat, stops[:, 0], stops[:, 3]).reshape(h.shape)
        rgb = np.stack([r, g, b], axis=-1).astype("uint8")
        return Image.fromarray(rgb, mode="RGB")

    # ── Lesion bbox & crop ───────────────────────────────────────────────

    def _focus_score(self, heat: np.ndarray, bbox: Optional[list[int]]) -> float:
        total = float(heat.sum())
        if total <= 1e-6 or not bbox:
            return 0.0
        left, top, right, bottom = bbox
        focused = float(heat[top:bottom + 1, left:right + 1].sum())
        return round(max(0.0, min(focused / total, 1.0)), 4)

    def _lesion_bbox(self, heat: np.ndarray) -> Optional[list[int]]:
        if heat.size == 0 or float(heat.max()) <= 1e-6:
            return None
        threshold = max(0.58, float(np.quantile(heat[heat > 0], 0.82))) if np.any(heat > 0) else 0.58
        component = self._best_dense_component(heat >= threshold, heat)
        if not component.any():
            component = self._largest_component(heat >= threshold)
        ys, xs = np.where(component)
        if len(xs) == 0 or len(ys) == 0:
            return None
        h, w = heat.shape
        pad = max(40, int(min(w, h) * 0.12))
        left   = max(0,     int(xs.min()) - pad)
        top    = max(0,     int(ys.min()) - pad)
        right  = min(w - 1, int(xs.max()) + pad)
        bottom = min(h - 1, int(ys.max()) + pad)
        return [left, top, right, bottom]

    def _lesion_crop(self, image: Image.Image, bbox: Optional[list[int]]) -> Optional[Image.Image]:
        if not bbox:
            return None
        left, top, right, bottom = bbox
        if right <= left or bottom <= top:
            return None
        crop = image.crop((left, top, right + 1, bottom + 1))
        w, h = crop.size
        scale = max(1, 600 // max(w, h))
        if scale > 1:
            crop = crop.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
        crop.thumbnail((800, 800), Image.Resampling.LANCZOS)
        return crop

    # ── Utils ────────────────────────────────────────────────────────────

    def _normalize(self, arr: np.ndarray) -> np.ndarray:
        arr = np.nan_to_num(arr.astype("float32"))
        lo, hi = float(arr.min()), float(arr.max())
        if math.isclose(lo, hi):
            return np.zeros_like(arr)
        return (arr - lo) / (hi - lo)

    def _png_base64(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")