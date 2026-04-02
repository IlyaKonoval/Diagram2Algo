import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from unittest.mock import patch, MagicMock

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_inference():
    with patch("app.routes.extract.image_inference") as mock:
        mock.return_value = '{"diagram_type": "sequence", "steps": [{"number": 1, "action": "Test step"}], "confidence": 0.9}'
        yield mock


@pytest.fixture
def mock_warmup():
    with patch("app.llm.factory.warmup") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def sample_image():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "model" in data


class TestExtractEndpoint:
    def test_extract_requires_file(self, client):
        response = client.post("/api/extract")
        assert response.status_code == 422

    def test_extract_rejects_non_image(self, client):
        response = client.post(
            "/api/extract",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert response.status_code == 400

    def test_extract_accepts_image(self, client, sample_image, mock_inference, mock_warmup):
        response = client.post(
            "/api/extract",
            files={"file": ("test.png", sample_image, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "source_file" in data


class TestGenerateEndpoint:
    def test_generate_sequence(self, client):
        response = client.post(
            "/api/generate",
            json={
                "steps": [
                    {"number": 1, "actor": "User", "action": "Request", "target": "Server"},
                ],
                "diagram_type": "sequence",
                "title": "Test",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "plantuml_code" in data
        assert "@startuml" in data["plantuml_code"]

    def test_generate_activity(self, client):
        response = client.post(
            "/api/generate",
            json={
                "steps": [
                    {"number": 1, "action": "First action"},
                    {"number": 2, "action": "Second action"},
                ],
                "diagram_type": "activity",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "start" in data["plantuml_code"]
        assert "stop" in data["plantuml_code"]
