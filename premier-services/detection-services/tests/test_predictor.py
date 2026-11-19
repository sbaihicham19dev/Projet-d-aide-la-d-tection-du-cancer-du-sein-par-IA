"""
Tests d'intégration — Detection Service
Lancer avec : pytest tests/ -v
"""
import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# ── Fixture : mock du Predictor ───────────────────────────────────────────────

FAKE_RESULT = {
    "class": "Cancer",
    "confidence": 0.87,
    "probabilities": {"Cancer": 0.87, "Non-Cancer": 0.13},
}


@pytest.fixture
def mock_predictor():
    pred = MagicMock()
    pred.is_loaded = True
    pred.predict.return_value = FAKE_RESULT
    return pred


@pytest.fixture
def client(mock_predictor):
    """Client de test avec le modèle mocké."""
    with patch("app.predictor.Predictor.load", return_value=None):
        from app.main import app, predictor
        app.state.predictor = mock_predictor
        predictor.is_loaded = True

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_image_bytes(size=(224, 224)) -> bytes:
    """Crée une image PNG synthétique en mémoire."""
    img = Image.new("RGB", size, color=(128, 64, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["model_loaded"] is True
        assert data["status"] in ("ok", "degraded")


class TestPredict:
    def test_predict_returns_200(self, client):
        img_bytes = _make_image_bytes()
        r = client.post(
            "/api/v1/predict",
            files={"file": ("test.png", img_bytes, "image/png")},
        )
        assert r.status_code == 200

    def test_predict_schema(self, client):
        img_bytes = _make_image_bytes()
        r = client.post(
            "/api/v1/predict",
            files={"file": ("test.png", img_bytes, "image/png")},
        )
        data = r.json()
        assert "predicted_class" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert "prediction_id" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_class_value(self, client):
        img_bytes = _make_image_bytes()
        r = client.post(
            "/api/v1/predict",
            files={"file": ("test.png", img_bytes, "image/png")},
        )
        assert r.json()["predicted_class"] in ("Cancer", "Non-Cancer")

    def test_predict_empty_file_returns_400(self, client):
        r = client.post(
            "/api/v1/predict",
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert r.status_code == 400

    def test_predict_invalid_file_returns_422(self, client):
        r = client.post(
            "/api/v1/predict",
            files={"file": ("bad.png", b"not-an-image", "image/png")},
        )
        assert r.status_code == 422


class TestBatchPredict:
    def test_batch_two_images(self, client):
        img = _make_image_bytes()
        r = client.post(
            "/api/v1/predict/batch",
            files=[
                ("files", ("a.png", img, "image/png")),
                ("files", ("b.png", img, "image/png")),
            ],
        )
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_batch_limit_exceeded(self, client):
        img = _make_image_bytes()
        files = [("files", (f"{i}.png", img, "image/png")) for i in range(17)]
        r = client.post("/api/v1/predict/batch", files=files)
        assert r.status_code == 400