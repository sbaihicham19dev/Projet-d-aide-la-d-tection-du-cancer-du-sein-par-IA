"""
test_sizer.py
--------------
Tests unitaires pour le Sizer (px → cm + TNM).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.sizer import Sizer, classify_tnm, DEFAULT_PIXEL_SPACING_MM


def test_classify_tnm():
    assert classify_tnm(0.3)[0] == "T1a"
    assert classify_tnm(0.7)[0] == "T1b"
    assert classify_tnm(1.5)[0] == "T1c"
    assert classify_tnm(3.0)[0] == "T2"
    assert classify_tnm(6.0)[0] == "T3"
    print("✅ test_classify_tnm passé")


def test_calculate_from_area_pct():
    sizer = Sizer()
    sizer.load()

    result = sizer.calculate_from_area_pct(
        tumor_area_pct   = 35.0,
        pixel_spacing_mm = DEFAULT_PIXEL_SPACING_MM,
        original_size_px = 224,
    )

    assert result.area_pct  == 35.0
    assert result.diameter_cm > 0
    assert result.area_cm2  > 0
    assert result.tnm_stage in ["T1a", "T1b", "T1c", "T2", "T3"]
    print(f"✅ test_calculate_from_area_pct : diam={result.diameter_cm} cm  TNM={result.tnm_stage}")


def test_no_tumor():
    sizer = Sizer()
    sizer.load()

    result = sizer.calculate_from_area_pct(
        tumor_area_pct   = 0.0,
        pixel_spacing_mm = DEFAULT_PIXEL_SPACING_MM,
        original_size_px = 224,
    )

    assert result.tnm_stage == "T0"
    assert result.diameter_cm == 0.0
    print("✅ test_no_tumor passé")


def test_pixel_spacing_effect():
    sizer = Sizer()
    sizer.load()

    r1 = sizer.calculate_from_area_pct(35.0, pixel_spacing_mm=0.05)
    r2 = sizer.calculate_from_area_pct(35.0, pixel_spacing_mm=0.10)

    assert r2.diameter_cm > r1.diameter_cm
    print(f"✅ test_pixel_spacing_effect : 0.05mm={r1.diameter_cm}cm  0.10mm={r2.diameter_cm}cm")


if __name__ == "__main__":
    print("🧪 Lancement des tests...\n")
    test_classify_tnm()
    test_calculate_from_area_pct()
    test_no_tumor()
    test_pixel_spacing_effect()
    print("\n✅ Tous les tests passés !")