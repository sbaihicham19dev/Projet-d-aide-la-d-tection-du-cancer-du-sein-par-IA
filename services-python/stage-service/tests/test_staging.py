"""
test_staging.py — Tests unitaires pour le staging TNM
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.staging import compute_stage, get_t_stage, stage_from_pipeline


def test_get_t_stage():
    assert get_t_stage(0.0)  == "T0"
    assert get_t_stage(0.3)  == "T1a"
    assert get_t_stage(0.7)  == "T1b"
    assert get_t_stage(1.5)  == "T1c"
    assert get_t_stage(3.0)  == "T2"
    assert get_t_stage(6.0)  == "T3"
    print("✅ test_get_t_stage passé")


def test_stage_IA():
    r = compute_stage("T1c", "N0", "M0")
    assert r.stage == "IA"
    assert r.stage_roman == "I"
    print(f"✅ test_stage_IA : {r.stage} — {r.prognosis}")


def test_stage_IIA():
    r = compute_stage("T2", "N0", "M0")
    assert r.stage == "IIA"
    print(f"✅ test_stage_IIA : {r.stage} — {r.prognosis}")


def test_stage_IIB():
    r = compute_stage("T3", "N0", "M0")
    assert r.stage == "IIB"
    print(f"✅ test_stage_IIB : {r.stage} — {r.prognosis}")


def test_stage_IV():
    r = compute_stage("T2", "N1", "M1")
    assert r.stage == "IV"
    print(f"✅ test_stage_IV : {r.stage} — {r.prognosis}")


def test_stage_from_pipeline():
    r = stage_from_pipeline(
        diameter_cm          = 1.57,
        classification_class = "Malignant",
        birads_score         = 4,
        n_stage              = "N0",
        m_stage              = "M0",
    )
    assert r.stage in ["IA", "IB", "IIA"]
    assert r.confidence > 0.7
    print(f"✅ test_stage_from_pipeline : Stade {r.stage}  conf={r.confidence}")


if __name__ == "__main__":
    print("🧪 Lancement des tests...\n")
    test_get_t_stage()
    test_stage_IA()
    test_stage_IIA()
    test_stage_IIB()
    test_stage_IV()
    test_stage_from_pipeline()
    print("\n✅ Tous les tests passés !")