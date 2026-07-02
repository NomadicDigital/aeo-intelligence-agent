import logging
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, HttpUrl

from graph import app as graph_app

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("agents").setLevel(logging.INFO)

app = FastAPI()

# --------------------------------------------------
# CORS
# --------------------------------------------------

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# --------------------------------------------------
# API Key auth
# --------------------------------------------------

API_KEY = os.getenv("INTERNAL_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(key: str = Security(api_key_header)):
    if not API_KEY:
        return  # auth disabled if no key configured
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

# --------------------------------------------------
# Routes
# --------------------------------------------------

class ReportRequest(BaseModel):
    url: HttpUrl

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/generate_report")
async def generate_report(request: ReportRequest, _ = Security(require_api_key)):

    url_str = str(request.url)

    try:
        result = await graph_app.ainvoke({
            "input_url": url_str,
            "email": "",
            "errors": [],
            "business_name": "",
            "description": "",
            "competitors": [],
            "core_queries": [],
            "llms_txt": {},
            "llms_full_txt": {},
            "robots_txt": {},
            "schema": {},
            "prospect_visibility": {},
            "competitor_visibility": {},
            "raw_html": None,
            "key_improvements": [],
            "visibility_insight": "",
            "quick_win": "",
            "overall_score": 0,
            "high_level_summary": "",
            "pdf_path": ""
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Report generation failed: {e}") from e

    pdf_path = result.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        errors = result.get("errors") or ["Report generation did not produce a PDF."]
        raise HTTPException(status_code=422, detail="; ".join(errors))

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=Path(pdf_path).name,
    )
