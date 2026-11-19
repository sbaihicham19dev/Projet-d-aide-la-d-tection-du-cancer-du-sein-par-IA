"""
staging.py — Classification TNM AJCC 8e édition

Stades :
    0    → Carcinome in situ
    IA   → T1 N0 M0
    IB   → T0/T1 N1mi M0
    IIA  → T0/T1 N1 M0 | T2 N0 M0
    IIB  → T2 N1 M0 | T3 N0 M0
    IIIA → T0-T3 N2 M0 | T3 N1 M0
    IIIB → T4 N0-N2 M0
    IIIC → Tout T N3 M0
    IV   → Tout T Tout N M1
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class StagingResult:
    t_stage:      str
    n_stage:      str
    m_stage:      str
    stage:        str    # "0","IA","IB","IIA","IIB","IIIA","IIIB","IIIC","IV"
    stage_roman:  str    # "I","II","III","IV"
    description:  str
    treatment:    str
    prognosis:    str
    confidence:   float


def get_t_stage(diameter_cm: float, tnm_stage: Optional[str] = None) -> str:
    if tnm_stage:
        return tnm_stage
    if diameter_cm == 0:   return "T0"
    if diameter_cm < 0.5:  return "T1a"
    if diameter_cm < 1.0:  return "T1b"
    if diameter_cm < 2.0:  return "T1c"
    if diameter_cm < 5.0:  return "T2"
    return "T3"


def compute_stage(t: str, n: str = "N0", m: str = "M0", conf: float = 0.8) -> StagingResult:

    if m == "M1":
        return StagingResult(t, n, m, "IV", "IV",
            "Cancer métastatique — dissémination à distance",
            "Chimiothérapie systémique, thérapies ciblées, immunothérapie",
            "Survie à 5 ans : ~28%", conf)

    T1 = t in ("T1", "T1a", "T1b", "T1c")
    T2 = t == "T2"
    T3 = t == "T3"
    T4 = t == "T4"
    T01 = t in ("T0", "T1", "T1a", "T1b", "T1c")

    if t in ("Tis", "T0") and n == "N0":
        return StagingResult(t, "N0", "M0", "0", "0",
            "Carcinome in situ — non invasif",
            "Chirurgie conservatrice ± radiothérapie",
            "Survie à 5 ans : ~99%", conf)

    if T1 and n == "N0":
        return StagingResult(t, "N0", "M0", "IA", "I",
            "Cancer localisé — petite tumeur sans atteinte ganglionnaire",
            "Chirurgie + radiothérapie ± hormonothérapie",
            "Survie à 5 ans : ~99%", conf)

    if T01 and n == "N1mi":
        return StagingResult(t, "N1mi", "M0", "IB", "I",
            "Cancer localisé avec micro-métastases ganglionnaires",
            "Chirurgie + radiothérapie + chimiothérapie adjuvante",
            "Survie à 5 ans : ~99%", conf)

    if (T01 and n == "N1") or (T2 and n == "N0"):
        return StagingResult(t, n, "M0", "IIA", "II",
            "Cancer localement avancé — atteinte ganglionnaire limitée",
            "Chirurgie + chimiothérapie adjuvante + radiothérapie",
            "Survie à 5 ans : ~86%", conf)

    if (T2 and n == "N1") or (T3 and n == "N0"):
        return StagingResult(t, n, "M0", "IIB", "II",
            "Cancer localement avancé — tumeur plus grande",
            "Chimiothérapie néoadjuvante + chirurgie + radiothérapie",
            "Survie à 5 ans : ~73%", conf)

    if n == "N2" or (T3 and n == "N1"):
        return StagingResult(t, n, "M0", "IIIA", "III",
            "Cancer avancé — atteinte ganglionnaire importante",
            "Chimiothérapie néoadjuvante + mastectomie + radiothérapie",
            "Survie à 5 ans : ~56%", conf)

    if T4 and n in ("N0", "N1", "N2"):
        return StagingResult(t, n, "M0", "IIIB", "III",
            "Cancer avancé — extension à la paroi thoracique ou peau",
            "Chimiothérapie + radiothérapie + chirurgie si possible",
            "Survie à 5 ans : ~49%", conf)

    if n == "N3":
        return StagingResult(t, "N3", "M0", "IIIC", "III",
            "Cancer avancé — atteinte ganglionnaire étendue",
            "Chimiothérapie + radiothérapie étendue",
            "Survie à 5 ans : ~49%", conf)

    return StagingResult(t, n, m, "IIA", "II",
        "Cancer localement avancé",
        "Évaluation oncologique complète recommandée",
        "Variable selon les caractéristiques tumorales",
        round(conf * 0.7, 3))


def stage_from_pipeline(
    diameter_cm:          float = 0.0,
    tnm_stage:            Optional[str] = None,
    classification_class: Optional[str] = None,
    birads_score:         Optional[int] = None,
    n_stage:              str = "N0",
    m_stage:              str = "M0",
) -> StagingResult:
    t    = get_t_stage(diameter_cm, tnm_stage)
    conf = 0.75
    if diameter_cm > 0:        conf += 0.10
    if classification_class:   conf += 0.05
    if birads_score and birads_score >= 4: conf += 0.05
    return compute_stage(t, n_stage, m_stage, round(min(conf, 0.95), 3))