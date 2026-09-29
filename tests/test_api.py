from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import main
from main import app

TEST_API_KEY = "test-key"

client = TestClient(app, headers={"X-API-Key": TEST_API_KEY})


@pytest.fixture(autouse=True)
def fixed_api_key(monkeypatch):
    """
    Pin the API key so the tests don't depend on whatever INTERNAL_API_KEY
    load_dotenv() picked up from a local .env.
    """
    monkeypatch.setattr(main, "API_KEY", TEST_API_KEY)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_report_rejects_wrong_api_key():
    response = client.post(
        "/generate_report",
        json={"url": "https://example.com"},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 403


def test_generate_report_returns_pdf(monkeypatch, tmp_path):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")

    monkeypatch.setattr(
        main.graph_app,
        "ainvoke",
        AsyncMock(return_value={"pdf_path": str(pdf_path), "errors": []}),
    )

    response = client.post("/generate_report", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 fake pdf content"
    assert not pdf_path.exists()


def test_generate_report_returns_422_when_no_pdf_produced(monkeypatch):
    monkeypatch.setattr(
        main.graph_app,
        "ainvoke",
        AsyncMock(return_value={"pdf_path": "", "errors": ["Could not scrape https://example.com"]}),
    )

    response = client.post("/generate_report", json={"url": "https://example.com"})

    assert response.status_code == 422
    assert "Could not scrape" in response.json()["detail"]


def test_generate_report_returns_502_on_pipeline_crash(monkeypatch):
    monkeypatch.setattr(
        main.graph_app,
        "ainvoke",
        AsyncMock(side_effect=RuntimeError("graph exploded")),
    )

    response = client.post("/generate_report", json={"url": "https://example.com"})

    assert response.status_code == 502
    assert "graph exploded" in response.json()["detail"]
