from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import main
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


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
