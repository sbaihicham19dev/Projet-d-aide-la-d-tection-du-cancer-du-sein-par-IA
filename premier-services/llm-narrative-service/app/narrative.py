import os
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    import httpx
except Exception:  # pragma: no cover - optional when rules mode is used
    httpx = None

from app.schemas import NarrativeResponse


class NarrativeGenerator:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "").rstrip("/")
        self.model = os.getenv("NARRATIVE_MODEL", "rules-structured")
        self.timeout = float(os.getenv("NARRATIVE_TIMEOUT_SECONDS", "20"))

    @property
    def llm_enabled(self) -> bool:
        return bool(httpx and self.ollama_url and self.model != "rules-structured")

    async def generate(self, report: Dict[str, Any], language: str = "fr", include_disclaimer: bool = True) -> NarrativeResponse:
        if self.llm_enabled:
            text = await self._generate_with_ollama(report, language)
            if text:
                return self._from_text(report, text, language)
        return self._generate_rules(report, language, include_disclaimer)

    async def _generate_with_ollama(self, report: Dict[str, Any], language: str) -> str:
        prompt = (
            "Transform this breast-cancer AI pipeline JSON into a concise structured clinical report. "
            "Do not chat. Do not invent missing findings. Language: "
            f"{language}. JSON: {report}"
        )
        if httpx is None:
            return ""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return str(response.json().get("response", "")).strip()
        except Exception:
            return ""

    def _generate_rules(self, report: Dict[str, Any], language: str, include_disclaimer: bool) -> NarrativeResponse:
        prediction_id = str(report.get("prediction_id") or "unknown")
        filename      = str(report.get("filename") or "unknown")
        stage         = report.get("stage") or {}
        birads        = report.get("birads") or {}
        classification = report.get("classification") or {}
        localization  = report.get("localization") or {}
        tumorsize     = report.get("tumorsize") or {}

        birads_score  = birads.get("birads_score", -1)
        birads_cat    = birads.get("birads_category", str(birads_score))
        det_class     = str(report.get("predicted_class") or "")
        det_conf      = float(report.get("confidence") or 0.0)
        cls_class     = str(classification.get("predicted_class") or "")
        cls_conf      = float(classification.get("confidence") or 0.0)

        # ── Détection de la discordance ──────────────────────────────────
        is_discordant = (
            det_class == "Cancer"
            and cls_class == "Benign"
            and cls_conf >= 0.75
        )

        # ── Findings ─────────────────────────────────────────────────────
        findings: List[str] = []

        # Résumé principal
        if report.get("clinical_summary"):
            findings.append(str(report["clinical_summary"]))

        # Classification lésionnelle
        if cls_class:
            findings.append(
                f"Classification lésionnelle: {cls_class} avec confiance {cls_conf:.4f}."
            )

        # Note de discordance explicite
        if is_discordant:
            findings.append(
                f"Discordance détection/classification: détection signale Cancer ({det_conf:.2f}) "
                f"mais classification indique Bénin ({cls_conf:.2f}). "
                f"La classification est privilégiée (confiance supérieure)."
            )

        # BI-RADS
        if birads_cat or birads_score is not None:
            findings.append(
                f"Évaluation BI-RADS: {birads_cat}; "
                f"recommandation: {birads.get('recommendation', 'à confirmer')}."
            )

        # Localisation
        loc_label = localization.get("quadrant_fr") or localization.get("quadrant_name")
        if loc_label:
            findings.append(f"Localisation estimée: {loc_label}.")

        # Taille tumorale — uniquement si cancer suspecté (BI-RADS ≥ 4)
        if birads_score >= 4 and tumorsize.get("diameter_cm"):
            findings.append(
                f"Taille tumorale estimée: {float(tumorsize['diameter_cm']):.2f} cm "
                f"({tumorsize.get('tnm_stage', 'T?')})."
            )

        # ── Stade TNM — uniquement si BI-RADS ≥ 4 ───────────────────────
        if birads_score >= 4:
            stage_summary = (
                f"Stade TNM estimé: {stage.get('stage', 'indéterminé')} "
                f"({stage.get('t_stage', 'T?')}"
                f"{stage.get('n_stage', 'N?')}"
                f"{stage.get('m_stage', 'M?')})."
            )
        else:
            stage_summary = "Stade TNM: non applicable (lésion probablement bénigne)."

        # ── Impression ───────────────────────────────────────────────────
        impression = self._impression(report, birads_score, is_discordant)

        # ── Recommandations ──────────────────────────────────────────────
        recommendations = list(report.get("recommendations") or [])
        if not recommendations:
            recommendations = self._default_recommendations(birads_score, is_discordant)

        # ── Limitations ──────────────────────────────────────────────────
        limitations = list(report.get("quality_warnings") or [])

        if det_conf < 0.60:
            limitations.append("Confiance faible pour la détection.")
        if is_discordant:
            limitations.append(
                "Résultats discordants: détection cancer mais classification bénigne. "
                "BI-RADS calculé selon la classification (plus confiante)."
            )
        if include_disclaimer:
            limitations.append(
                "Compte rendu généré par pipeline IA; "
                "validation radiologique et confrontation clinique obligatoires."
            )

        # ── Texte narratif final ─────────────────────────────────────────
        narrative_text = "\n".join([
            "Compte rendu structuré",
            f"Image: {filename}",
            f"Impression: {impression}",
            "Constatations:",
            *[f"- {item}" for item in findings],
            stage_summary,
            "Recommandations:",
            *[f"- {item}" for item in recommendations],
            "Limites:",
            *[f"- {item}" for item in limitations],
        ])

        return NarrativeResponse(
            prediction_id=prediction_id,
            filename=filename,
            language=language,
            title="Compte rendu IA mammographie",
            impression=impression,
            findings=findings,
            stage_summary=stage_summary,
            recommendations=recommendations,
            limitations=limitations,
            narrative_text=narrative_text,
            model="rules-structured",
            timestamp=datetime.now(timezone.utc),
        )

    def _impression(self, report: Dict[str, Any], birads_score: int, is_discordant: bool) -> str:
        """
        Génère l'impression clinique selon le BI-RADS réel.
        """
        stage_label = (report.get("stage") or {}).get("stage", "indéterminé")

        if birads_score == 0:
            return "Résultat IA incomplet; imagerie complémentaire nécessaire avant conclusion."
        if birads_score == 1:
            return "Mammographie négative; aucune anomalie détectée."
        if birads_score == 2:
            return "Anomalie bénigne; pas de risque de malignité."
        if birads_score == 3:
            if is_discordant:
                return (
                    "Lésion probablement bénigne sur la base de la classification IA; "
                    "suivi mammographique à 6 mois recommandé."
                )
            return "Lésion probablement bénigne; risque de malignité < 2%; suivi à 6 mois."
        if birads_score == 4:
            return f"Suspicion intermédiaire; stade estimé {stage_label}, confirmation histologique recommandée."
        if birads_score == 5:
            return f"Suspicion élevée de malignité; stade estimé {stage_label}; biopsie obligatoire."
        if birads_score == 6:
            return f"Cancer confirmé histologiquement; stade {stage_label}; prise en charge oncologique immédiate."

        # Fallback (ne devrait pas arriver)
        risk = report.get("risk_level", "unknown")
        if risk == "high":
            return f"Suspicion élevée nécessitant une prise en charge rapide; stade estimé {stage_label}."
        if risk == "moderate":
            return f"Suspicion intermédiaire; stade estimé {stage_label}, confirmation recommandée."
        return f"Risque faible selon les résultats disponibles; stade estimé {stage_label}."

    def _default_recommendations(self, birads_score: int, is_discordant: bool) -> List[str]:
        """
        Recommandations par défaut adaptées au BI-RADS.
        """
        recs = ["Valider les résultats IA avec un radiologue avant toute utilisation clinique."]

        if birads_score <= 2:
            recs.append("Mammographie de contrôle annuelle.")
        elif birads_score == 3:
            recs.append("Suivi mammographique à 6 mois.")
            if is_discordant:
                recs.append("Corrélation clinique recommandée en raison de la discordance détection/classification.")
        elif birads_score == 4:
            recs.append("Biopsie recommandée pour confirmation histologique.")
        elif birads_score == 5:
            recs.append("Biopsie obligatoire en urgence.")
        elif birads_score == 6:
            recs.append("Orientation oncologique immédiate.")

        return recs

    def _from_text(self, report: Dict[str, Any], text: str, language: str) -> NarrativeResponse:
        lines = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
        return NarrativeResponse(
            prediction_id=str(report.get("prediction_id") or "unknown"),
            filename=str(report.get("filename") or "unknown"),
            language=language,
            title="Compte rendu IA mammographie",
            impression=lines[0] if lines else "Compte rendu généré.",
            findings=lines[1:6] if len(lines) > 1 else [],
            stage_summary=str((report.get("stage") or {}).get("description") or ""),
            recommendations=list(report.get("recommendations") or []),
            limitations=list(report.get("quality_warnings") or []),
            narrative_text=text,
            model=self.model,
            timestamp=datetime.now(timezone.utc),
        )