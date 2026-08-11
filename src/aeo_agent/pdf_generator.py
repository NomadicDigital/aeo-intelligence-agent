import os
import sys
from datetime import datetime
from pathlib import Path

# On macOS, Homebrew installs pango/gobject under /opt/homebrew/lib which is not
# on the default dyld search path. Set it before WeasyPrint's cffi calls dlopen.
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    existing = os.environ.get("DYLD_LIBRARY_PATH", "")
    if homebrew_lib not in existing:
        os.environ["DYLD_LIBRARY_PATH"] = f"{homebrew_lib}:{existing}".rstrip(":")

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent / "templates"
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"


def generate_pdf(
    business_name: str,
    input_url: str,
    overall_score: int,
    high_level_summary: str,
    key_improvements: list,
    visibility_insight: str,
    quick_win: str,
    robots_txt: dict,
    llms_txt: dict,
    llms_full_txt: dict,
    schema: dict,
    prospect_visibility: dict,
    competitor_visibility: dict,
) -> str:
    """Render the Jinja2 HTML template and write a PDF. Returns the output file path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    prospect_score = round(prospect_visibility.get("total_prospect_score", 0))
    query_count = len(prospect_visibility.get("query_breakdown", {}))

    sorted_competitors = sorted(competitor_visibility.items(), key=lambda item: item[1], reverse=True)
    competitor_bars = [
        (name, round(score), max(round(score), 2) if round(score) == 0 else round(score))
        for name, score in sorted_competitors
    ]

    if overall_score >= 7:
        score_verdict = "Strong AEO foundation"
    elif overall_score >= 4:
        score_verdict = "Partial visibility — room to grow"
    else:
        score_verdict = "Significant visibility gaps"

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html")
    html_content = template.render(
        business_name=business_name,
        input_url=input_url,
        overall_score=overall_score,
        score_percent=round(overall_score / 10 * 100),
        score_verdict=score_verdict,
        high_level_summary=high_level_summary,
        improvements=key_improvements,
        visibility_insight=visibility_insight,
        quick_win=quick_win,
        robots_txt=robots_txt,
        llms_txt=llms_txt,
        llms_full_txt=llms_full_txt,
        schema=schema,
        prospect_score=prospect_score,
        query_count=query_count,
        competitor_bars=competitor_bars,
        generated_date=datetime.now().strftime("%d %B %Y"),
    )

    safe_name = "".join(c if c.isalnum() else "_" for c in business_name).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"{safe_name}_{timestamp}.pdf"

    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(str(output_path))
    return str(output_path)