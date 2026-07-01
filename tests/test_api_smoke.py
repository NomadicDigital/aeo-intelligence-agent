import sys
sys.path.insert(0, 'src/aeo_agent')

from pathlib import Path

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

print("\n=== ROOT CHECK ===")
root_response = client.get("/")
print("Status:", root_response.status_code)
print("Body:", root_response.json())

print("\n=== GENERATE REPORT ===")
response = client.post(
    "/generate_report",
    json={"url": "https://www.fallowfieldscamping.com"},
)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("content-type"))

if response.status_code == 200:
    output_path = Path("reports/test_api_output.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    print("Content-Disposition:", response.headers.get("content-disposition"))
    print("PDF saved to:", output_path)
else:
    print("Error detail:", response.json())
