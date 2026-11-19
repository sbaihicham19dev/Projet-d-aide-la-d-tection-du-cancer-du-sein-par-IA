"""
tests/test_predictor.py
Test rapide du predictor avec une image ou un fichier DICOM.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.predictor import predictor

def test_with_file(path: str):
    with open(path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(path)
    result   = predictor.predict(file_bytes, filename)

    print(f"\nFichier    : {filename}")
    print(f"Label      : {result['label']}")
    print(f"Confidence : {result['confidence']*100:.1f}%")
    print(f"Probabilites :")
    for cls, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"  {cls:15s} : {prob*100:.1f}%  {bar}")


if __name__ == "__main__":
    # Test avec le fichier DICOM sample
    test_path = "tests/sample.dcm"

    if os.path.exists(test_path):
        test_with_file(test_path)
    else:
        print(f"Fichier introuvable : {test_path}")
        print("Usage : python tests/test_predictor.py")
        print("        ou modifier test_path dans le script")