import pytest
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian
import io
import struct

from app.predictor import DetectionPredictor
from app.schemas import OutputDetection


def create_fake_dicom() -> bytes:
    """Génère un fichier DICOM minimal pour les tests."""
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1"
    file_meta.MediaStorageSOPInstanceUID = "1.2.3"
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.PatientName = "Test^Patient"
    ds.PatientID = "TEST001"
    ds.Rows = 224
    ds.Columns = 224
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.PixelSpacing = [0.1, 0.1]

    # Pixel data aléatoire 224x224
    pixel_array = np.random.randint(0, 4095, (224, 224), dtype=np.uint16)
    ds.PixelData = pixel_array.tobytes()

    buffer = io.BytesIO()
    pydicom.dcmwrite(buffer, ds)
    return buffer.getvalue()


class TestDetectionPredictor:

    def setup_method(self):
        """Instancie le predictor avant chaque test."""
        self.predictor = DetectionPredictor()
        self.fake_dicom = create_fake_dicom()

    def test_predict_returns_dict(self):
        """Le predictor retourne bien un dictionnaire."""
        result = self.predictor.predict(self.fake_dicom)
        assert isinstance(result, dict)

    def test_predict_has_required_keys(self):
        """Les clés obligatoires sont présentes."""
        result = self.predictor.predict(self.fake_dicom)
        assert "prediction" in result
        assert "confidence" in result
        assert "model_version" in result

    def test_prediction_is_binary(self):
        """La prédiction est Cancer ou Non-Cancer."""
        result = self.predictor.predict(self.fake_dicom)
        assert result["prediction"] in ["Cancer", "Non-Cancer"]

    def test_confidence_range(self):
        """La confiance est entre 0 et 1."""
        result = self.predictor.predict(self.fake_dicom)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_model_version(self):
        """La version du modèle est correcte."""
        result = self.predictor.predict(self.fake_dicom)
        assert result["model_version"] == "resnet50-v1.0"

    def test_invalid_bytes_raises(self):
        """Des bytes invalides lèvent une exception."""
        with pytest.raises(Exception):
            self.predictor.predict(b"not_a_dicom_file")


class TestSchemas:

    def test_output_detection_valid(self):
        """OutputDetection accepte des données valides."""
        output = OutputDetection(
            image_uuid="550e8400-e29b-41d4-a716-446655440000",
            patient_id="PAT-001",
            prediction="Cancer",
            confidence=0.96,
            model_version="resnet50-v1.0",
            status="success"
        )
        assert output.prediction == "Cancer"
        assert output.confidence == 0.96

    def test_confidence_out_of_range(self):
        """Confiance hors de [0,1] est rejetée."""
        with pytest.raises(Exception):
            OutputDetection(
                image_uuid="test",
                patient_id="PAT-001",
                prediction="Cancer",
                confidence=1.5,  # invalide
            )

    def test_invalid_prediction_label(self):
        """Label de prédiction invalide est rejeté."""
        with pytest.raises(Exception):
            OutputDetection(
                image_uuid="test",
                patient_id="PAT-001",
                prediction="Malin",  # invalide, doit être Cancer/Non-Cancer
                confidence=0.9,
            )
