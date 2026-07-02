"""
End-to-end smoke test — hits live APIs (Firecrawl, Anthropic).
Run manually: pytest tests/test_pipeline_smoke.py -v -s
Not included in the automated test suite (excluded via conftest.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "aeo_agent"))

from fastapi.testclient import TestClient
from main import app

TEST_URL = "https://www.fallowfieldscamping.com"

client = TestClient(app)


def test_full_pipeline():
    response = client.post("/generate_report", json={"url": TEST_URL})

    print("\n=== API ===")
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("content-type"))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.headers.get("content-type") == "application/pdf"

    output_path = Path("reports/smoke_test_output.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    print(f"PDF saved to: {output_path}")
