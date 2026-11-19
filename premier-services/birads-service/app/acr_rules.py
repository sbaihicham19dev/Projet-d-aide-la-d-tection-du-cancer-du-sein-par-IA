"""
ACR-inspired BI-RADS rules for the pipeline.

These rules are deliberately conservative when the detection service says
Cancer but the benign/malignant classifier disagrees. A medium-confidence
Benign result should not downgrade a Cancer detection to BI-RADS 3.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BIRADSResult:
    score: int
    category: str
    description: str
    malignancy_risk: str
    recommendation: str
    confidence: float


DETECTION_LOW = 0.55
DETECTION_HIGH = 0.80
DETECTION_VERY_HIGH = 0.85

CLASSIFICATION_STRONG_BENIGN = 0.85
CLASSIFICATION_HIGH = 0.85

TUMOR_AREA_MAX_PCT = 40.0


def _is_segmentation_aberrant(tumor_area_pct: Optional[float]) -> bool:
    return tumor_area_pct is not None and tumor_area_pct > TUMOR_AREA_MAX_PCT


def compute_birads(
    detection_class: str,
    detection_conf: float,
    classification_class: Optional[str] = None,
    classification_conf: Optional[float] = None,
    tumor_area_pct: Optional[float] = None,
) -> BIRADSResult:
    conf_cls = classification_conf or 0.0
    seg_aberrant = _is_segmentation_aberrant(tumor_area_pct)

    if detection_class == "Non-Cancer":
        if detection_conf >= 0.80:
            return BIRADSResult(
                1,
                "1",
                "Negatif - aucune anomalie detectee",
                "0%",
                "Mammographie annuelle de routine",
                round(detection_conf, 3),
            )
        if detection_conf >= 0.60:
            return BIRADSResult(
                2,
                "2",
                "Benin - anomalie benigne certaine",
                "0%",
                "Suivi de routine",
                round(detection_conf, 3),
            )
        return BIRADSResult(
            0,
            "0",
            "Resultat IA incertain - imagerie complementaire necessaire",
            "Indetermine",
            "Relecture radiologique et examen complementaire recommandes",
            round(detection_conf, 3),
        )

    if detection_class != "Cancer":
        return BIRADSResult(
            0,
            "0",
            "Resultat IA incertain - classe de detection inconnue",
            "Indetermine",
            "Relecture radiologique recommandee",
            round(detection_conf, 3),
        )

    if classification_class == "Benign":
        if (
            conf_cls >= CLASSIFICATION_STRONG_BENIGN
            and detection_conf < DETECTION_LOW
            and not seg_aberrant
        ):
            return BIRADSResult(
                3,
                "3",
                "Probablement benin - classification benigne forte",
                "<2%",
                "Suivi mammographique a 6 mois; correlation clinique recommandee",
                round((detection_conf + conf_cls) / 2, 3),
            )

        desc_extra = " avec segmentation non fiable" if seg_aberrant else ""
        return BIRADSResult(
            4,
            "4A",
            f"Faible suspicion - discordance detection cancer / classification benigne{desc_extra}",
            "2-10%",
            "Avis radiologique prioritaire; biopsie a considerer selon correlation clinique",
            round((detection_conf + conf_cls) / 2, 3),
        )

    if (
        detection_conf >= DETECTION_VERY_HIGH
        and classification_class == "Malignant"
        and conf_cls >= CLASSIFICATION_HIGH
    ):
        return BIRADSResult(
            6,
            "6",
            "Cancer confirme histologiquement",
            ">95%",
            "Prise en charge oncologique immediate",
            round((detection_conf + conf_cls) / 2, 3),
        )

    if (
        detection_conf >= DETECTION_HIGH
        and classification_class == "Malignant"
        and conf_cls >= 0.70
    ):
        return BIRADSResult(
            5,
            "5",
            "Tres suggestif de malignite",
            ">95%",
            "Biopsie obligatoire",
            round((detection_conf + conf_cls) / 2, 3),
        )

    if classification_class == "Malignant" and conf_cls >= 0.60:
        return BIRADSResult(
            4,
            "4C",
            "Suspicion elevee de malignite",
            "50-95%",
            "Biopsie fortement recommandee",
            round((detection_conf + conf_cls) / 2, 3),
        )

    if classification_class == "Malignant" and conf_cls >= 0.50:
        return BIRADSResult(
            4,
            "4B",
            "Suspicion moderee de malignite",
            "10-50%",
            "Biopsie recommandee",
            round((detection_conf + conf_cls) / 2, 3),
        )

    if classification_class == "Malignant":
        return BIRADSResult(
            4,
            "4A",
            "Faible suspicion de malignite",
            "2-10%",
            "Biopsie a considerer",
            round((detection_conf + conf_cls) / 2, 3),
        )

    if detection_conf >= DETECTION_HIGH:
        return BIRADSResult(
            4,
            "4B",
            "Suspicion - pas de classification disponible",
            "10-50%",
            "Biopsie recommandee; classification manquante",
            round(detection_conf, 3),
        )

    if detection_conf >= DETECTION_LOW:
        return BIRADSResult(
            4,
            "4A",
            "Faible suspicion - detection cancer sans confirmation fiable",
            "2-10%",
            "Avis radiologique prioritaire; biopsie a considerer",
            round(detection_conf, 3),
        )

    return BIRADSResult(
        0,
        "0",
        "Resultat IA incertain - confiance insuffisante",
        "Indetermine",
        "Relecture radiologique prioritaire; examen complementaire selon avis clinique",
        round(detection_conf, 3),
    )
