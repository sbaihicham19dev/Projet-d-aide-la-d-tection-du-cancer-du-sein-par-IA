"""
acr_rules.py — Règles ACR 2024 pour score BI-RADS (0-6)

Scores :
    0 → Incomplet
    1 → Négatif
    2 → Bénin
    3 → Probablement bénin (<2% malignité)
    4 → Suspicion (4A/4B/4C)
    5 → Très suggestif malignité (>95%)
    6 → Cancer confirmé
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class BIRADSResult:
    score:           int
    category:        str
    description:     str
    malignancy_risk: str
    recommendation:  str
    confidence:      float


def compute_birads(
    detection_class:      str,
    detection_conf:       float,
    classification_class: Optional[str]   = None,
    classification_conf:  Optional[float] = None,
    tumor_area_pct:       Optional[float] = None,
) -> BIRADSResult:

    # ── Non-Cancer ────────────────────────────────────────────────────────────
    if detection_class == "Non-Cancer":
        if detection_conf >= 0.80:
            return BIRADSResult(1, "1", "Négatif — aucune anomalie",
                                "0%", "Mammographie annuelle", detection_conf)
        if detection_conf >= 0.60:
            return BIRADSResult(2, "2", "Bénin — anomalie bénigne certaine",
                                "0%", "Suivi de routine", detection_conf)
        return BIRADSResult(0, "0", "Incomplet — imagerie complémentaire nécessaire",
                            "Indéterminé", "Échographie ou IRM recommandée", detection_conf)

    # ── Cancer détecté ────────────────────────────────────────────────────────
    conf_cls = classification_conf or 0.5

    if detection_conf >= 0.85 and classification_class == "Malignant" and conf_cls >= 0.85:
        return BIRADSResult(6, "6", "Cancer confirmé histologiquement",
                            ">95%", "Prise en charge oncologique immédiate",
                            round((detection_conf + conf_cls) / 2, 3))

    if detection_conf >= 0.75 and classification_class == "Malignant" and conf_cls >= 0.70:
        return BIRADSResult(5, "5", "Très suggestif de malignité",
                            ">95%", "Biopsie obligatoire",
                            round((detection_conf + conf_cls) / 2, 3))

    if classification_class == "Malignant" and conf_cls >= 0.60:
        return BIRADSResult(4, "4C", "Suspicion élevée de malignité",
                            "50-95%", "Biopsie fortement recommandée",
                            round((detection_conf + conf_cls) / 2, 3))

    if classification_class == "Malignant" and conf_cls >= 0.50:
        return BIRADSResult(4, "4B", "Suspicion modérée de malignité",
                            "10-50%", "Biopsie recommandée",
                            round((detection_conf + conf_cls) / 2, 3))

    if classification_class == "Malignant":
        return BIRADSResult(4, "4A", "Faible suspicion de malignité",
                            "2-10%", "Biopsie à considérer",
                            round((detection_conf + conf_cls) / 2, 3))

    if classification_class == "Benign" and conf_cls >= 0.70:
        return BIRADSResult(3, "3", "Probablement bénin",
                            "<2%", "Suivi mammographique à 6 mois",
                            round((detection_conf + conf_cls) / 2, 3))

    return BIRADSResult(4, "4A", "Anomalie suspecte — évaluation complémentaire",
                        "2-10%", "Consultation spécialisée recommandée",
                        detection_conf)