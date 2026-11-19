from dataclasses import dataclass
from typing import Optional


@dataclass
class StagingResult:
    t_stage: str
    n_stage: str
    m_stage: str
    stage: str
    stage_roman: str
    description: str
    treatment: str
    prognosis: str
    confidence: float


def get_t_stage(diameter_cm: float, tnm_stage: Optional[str] = None) -> str:
    if tnm_stage:
        return tnm_stage
    if diameter_cm <= 0:
        return "T0"
    if diameter_cm < 0.5:
        return "T1a"
    if diameter_cm < 1.0:
        return "T1b"
    if diameter_cm < 2.0:
        return "T1c"
    if diameter_cm < 5.0:
        return "T2"
    return "T3"


def compute_stage(t: str, n: str = "N0", m: str = "M0", conf: float = 0.8) -> StagingResult:
    t = (t or "T0").strip()
    n = (n or "N0").strip()
    m = (m or "M0").strip()
    conf = max(0.0, min(float(conf), 0.99))

    if m == "M1":
        return StagingResult(t, n, m, "IV", "IV",
                             "Metastatic disease suspected from supplied TNM inputs.",
                             "Urgent multidisciplinary oncology review; systemic workup required.",
                             "Depends on metastatic burden, receptors, and response to therapy.", conf)

    is_t1 = t in {"T1", "T1a", "T1b", "T1c"}
    is_t2 = t == "T2"
    is_t3 = t == "T3"
    is_t4 = t == "T4"
    is_t0_t1 = t in {"T0", "T1", "T1a", "T1b", "T1c"}

    if t in {"Tis", "T0"} and n == "N0":
        return StagingResult(t, n, m, "0", "0",
                             "In situ or no measurable invasive tumor with no nodal involvement.",
                             "Confirm pathology and manage according to breast unit protocol.",
                             "Excellent when confirmed as non-invasive.", conf)
    if is_t1 and n == "N0":
        return StagingResult(t, n, m, "IA", "I",
                             "Small localized invasive tumor without nodal involvement.",
                             "Breast-conserving surgery or mastectomy, then adjuvant therapy by profile.",
                             "Generally favorable; receptor status remains decisive.", conf)
    if is_t0_t1 and n == "N1mi":
        return StagingResult(t, n, m, "IB", "I",
                             "Localized tumor with nodal micrometastasis.",
                             "Surgery plus adjuvant treatment based on pathology and molecular markers.",
                             "Generally favorable with appropriate local and systemic treatment.", conf)
    if (is_t0_t1 and n == "N1") or (is_t2 and n == "N0"):
        return StagingResult(t, n, m, "IIA", "II",
                             "Early locally advanced pattern.",
                             "Multidisciplinary planning; surgery and adjuvant systemic therapy often considered.",
                             "Intermediate risk; refine after pathology.", conf)
    if (is_t2 and n == "N1") or (is_t3 and n == "N0"):
        return StagingResult(t, n, m, "IIB", "II",
                             "Larger tumor or limited nodal disease.",
                             "Consider neoadjuvant therapy depending on subtype and operability.",
                             "Intermediate risk; final prognosis depends on biology.", conf)
    if n == "N2" or (is_t3 and n == "N1"):
        return StagingResult(t, n, m, "IIIA", "III",
                             "Advanced regional disease pattern.",
                             "Neoadjuvant systemic therapy and regional treatment planning are commonly required.",
                             "Higher risk; specialist oncology review required.", conf)
    if is_t4 and n in {"N0", "N1", "N2"}:
        return StagingResult(t, n, m, "IIIB", "III",
                             "Tumor extension to skin or chest wall suspected.",
                             "Neoadjuvant systemic therapy and locoregional treatment planning.",
                             "Higher risk; treatment response is important.", conf)
    if n == "N3":
        return StagingResult(t, n, m, "IIIC", "III",
                             "Extensive regional nodal involvement.",
                             "Systemic therapy plus comprehensive locoregional management.",
                             "Higher risk; requires complete staging and subtype assessment.", conf)

    return StagingResult(t, n, m, "IIA", "II",
                         "Indeterminate TNM combination; conservative stage estimate.",
                         "Complete clinical, imaging, and pathology assessment recommended.",
                         "Cannot be estimated precisely from current inputs.", round(conf * 0.7, 3))


def stage_from_pipeline(
    diameter_cm: float = 0.0,
    tnm_stage: Optional[str] = None,
    classification_class: Optional[str] = None,
    birads_score: Optional[int] = None,
    n_stage: str = "N0",
    m_stage: str = "M0",
) -> StagingResult:
    t_stage = get_t_stage(diameter_cm, tnm_stage)
    confidence = 0.72
    if diameter_cm > 0:
        confidence += 0.10
    if classification_class:
        confidence += 0.05
    if birads_score is not None and birads_score >= 4:
        confidence += 0.05
    return compute_stage(t_stage, n_stage, m_stage, round(min(confidence, 0.95), 3))
