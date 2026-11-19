import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.schemas import AssembledReport, PipelineInputs, StageResponse
from app.staging import stage_from_pipeline


EXPECTED_RESULTS = [
    "detection",
    "classification",
    "segmentation",
    "birads",
    "localization",
    "tumorsize",
    "visualization",
]


class ReportAssembler:
    def assemble(self, payload: PipelineInputs) -> AssembledReport:
        prediction_id = payload.prediction_id or self._first_value(payload, "prediction_id") or str(uuid.uuid4())
        filename = payload.filename or self._first_value(payload, "filename") or "unknown"

        stage = stage_from_pipeline(
            diameter_cm=self._float_from(payload.tumorsize, "diameter_cm"),
            tnm_stage=self._str_from(payload.tumorsize, "tnm_stage"),
            classification_class=self._str_from(payload.classification, "predicted_class"),
            birads_score=self._int_from(payload.birads, "birads_score"),
            n_stage=payload.n_stage,
            m_stage=payload.m_stage,
        )
        stage_response = StageResponse(**stage.__dict__)

        missing = [name for name in EXPECTED_RESULTS if getattr(payload, name) is None]
        completeness = round((len(EXPECTED_RESULTS) - len(missing)) / len(EXPECTED_RESULTS), 3)
        warnings = self._quality_warnings(payload)
        recommendations = self._recommendations(payload, stage_response, warnings)

        return AssembledReport(
            prediction_id=prediction_id,
            filename=filename,
            status="complete" if not missing else "partial",
            completeness=completeness,
            missing_results=missing,
            risk_level=self._risk_level(payload, stage_response, warnings),
            clinical_summary=self._summary(payload, stage_response),
            recommendations=recommendations,
            quality_warnings=warnings,
            detection=payload.detection,
            classification=payload.classification,
            segmentation=self._strip_heavy_fields(payload.segmentation),
            birads=payload.birads,
            localization=payload.localization,
            tumorsize=payload.tumorsize,
            visualization=self._strip_heavy_fields(payload.visualization),
            stage=stage_response,
            timestamp=datetime.now(timezone.utc),
        )

    def _summary(self, payload: PipelineInputs, stage: StageResponse) -> str:
        detection_class = self._str_from(payload.detection, "predicted_class") or self._str_from(payload.detection, "class")
        detection_conf = self._float_from(payload.detection, "confidence")
        cls = self._str_from(payload.classification, "predicted_class")
        birads = self._str_from(payload.birads, "birads_category") or self._str_from(payload.birads, "birads_score")
        quadrant = self._str_from(payload.localization, "quadrant_fr") or self._str_from(payload.localization, "quadrant_name")
        diameter = self._float_from(payload.tumorsize, "diameter_cm")

        parts = []
        if detection_class:
            parts.append(f"Détection: {detection_class} ({detection_conf:.2f}).")
        if cls:
            parts.append(f"Classification: {cls}.")
        if birads:
            parts.append(f"BI-RADS: {birads}.")
        if quadrant:
            parts.append(f"Localisation: {quadrant}.")
        if diameter > 0:
            parts.append(f"Diamètre estimé: {diameter:.2f} cm.")
        parts.append(f"Stade TNM estimé: {stage.stage} ({stage.t_stage}{stage.n_stage}{stage.m_stage}).")
        return " ".join(parts)

    def _risk_level(self, payload: PipelineInputs, stage: StageResponse, warnings: List[str]) -> str:
        birads_score = self._int_from(payload.birads, "birads_score")
        cls = (self._str_from(payload.classification, "predicted_class") or "").lower()

        # Discordance détection/classification → toujours high (principe de précaution)
        has_discordance = any("discordants" in w for w in warnings)
        if has_discordance:
            return "high"

        if stage.stage_roman in {"III", "IV"} or birads_score >= 5:
            return "high"
        if stage.stage_roman == "II" or birads_score == 4 or cls == "malignant":
            return "moderate"
        return "low"

    def _recommendations(self, payload: PipelineInputs, stage: StageResponse, warnings: List[str]) -> List[str]:
        recs = ["Valider les résultats IA avec un radiologue avant toute utilisation clinique."]
        birads_score = self._int_from(payload.birads, "birads_score")

        # Recommandation spécifique discordance
        has_discordance = any("discordants" in w for w in warnings)
        if has_discordance:
            recs.append(
                "⚠ Discordance détection/classification détectée — "
                "une relecture radiologique manuelle est obligatoire avant tout diagnostic."
            )

        if birads_score >= 4:
            recs.append("Recommander une biopsie ou une confirmation histologique selon les recommandations BI-RADS.")
        if stage.stage_roman in {"III", "IV"}:
            recs.append("Demander une revue oncologique multidisciplinaire et un bilan d'extension complet.")
        if warnings:
            recs.append("Répéter ou relire les étapes de faible qualité avant le compte rendu final.")
        return recs

    def _quality_warnings(self, payload: PipelineInputs) -> List[str]:
        warnings: List[str] = []

        det_conf = self._float_from(payload.detection, "confidence")
        cls_conf = self._float_from(payload.classification, "confidence")

        if det_conf and det_conf < 0.6:
            warnings.append(f"Confiance faible pour la détection ({det_conf:.0%}).")
        if cls_conf and cls_conf < 0.6:
            warnings.append(f"Confiance faible pour la classification ({cls_conf:.0%}).")

        detection_class = (
            self._str_from(payload.detection, "predicted_class")
            or self._str_from(payload.detection, "class")
            or ""
        ).lower()
        cls = (self._str_from(payload.classification, "predicted_class") or "").lower()

        # Discordance — message enrichi avec les confidences
        if detection_class == "cancer" and cls in {"benign", "non-cancer", "normal"}:
            det_pct = f"{det_conf:.0%}" if det_conf else "N/A"
            cls_pct = f"{cls_conf:.0%}" if cls_conf else "N/A"
            warnings.append(
                f"Résultats discordants: détection Cancer ({det_pct}) "
                f"mais classification Bénigne ({cls_pct}). "
                f"Relecture radiologique obligatoire."
            )
        elif detection_class in {"non-cancer", "normal"} and cls in {"malignant", "cancer"}:
            det_pct = f"{det_conf:.0%}" if det_conf else "N/A"
            cls_pct = f"{cls_conf:.0%}" if cls_conf else "N/A"
            warnings.append(
                f"Résultats discordants: détection Négatif ({det_pct}) "
                f"mais classification Maligne ({cls_pct}). "
                f"Relecture radiologique obligatoire."
            )

        if payload.segmentation and self._float_from(payload.segmentation, "tumor_area_pct") <= 0:
            warnings.append("La segmentation n'a pas identifié de lésion mesurable.")
        if payload.visualization and self._float_from(payload.visualization, "focus_score") < 0.25:
            warnings.append("La heatmap de visualisation a un focus faible.")
        return warnings

    def _first_value(self, payload: PipelineInputs, key: str) -> Optional[str]:
        for name in EXPECTED_RESULTS:
            value = getattr(payload, name)
            if isinstance(value, dict) and value.get(key):
                return str(value[key])
        return None

    def _strip_heavy_fields(self, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        return {k: v for k, v in value.items() if k not in {"mask_base64", "overlay_base64", "heatmap_base64", "lesion_base64"}}

    def _str_from(self, data: Optional[Dict[str, Any]], key: str) -> Optional[str]:
        if not isinstance(data, dict) or data.get(key) is None:
            return None
        return str(data[key])

    def _float_from(self, data: Optional[Dict[str, Any]], key: str) -> float:
        if not isinstance(data, dict):
            return 0.0
        try:
            return float(data.get(key) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _int_from(self, data: Optional[Dict[str, Any]], key: str) -> int:
        if not isinstance(data, dict):
            return 0
        try:
            return int(data.get(key) or 0)
        except (TypeError, ValueError):
            return 0