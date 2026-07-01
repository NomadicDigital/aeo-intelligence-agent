from unittest.mock import MagicMock

from agents import report as report_module
from agents.report import generate_initial_score, report


def test_generate_initial_score_combines_signals():
    score = generate_initial_score(
        llms_txt=True,
        llms_full_text=False,
        schema=True,
        robots_txt=True,
        prospect_visibility_score=50,
    )

    # 1 (llms) + 3 (schema) + 2 (robots) + (50/100)*4 (visibility) = 8
    assert score == 8


def _extraction(**overrides):
    defaults = dict(
        overall_score=5,
        key_improvements="1. Do X\n2. Do Y",
        high_level_summary="Summary",
        visibility_insight="Insight",
        quick_win="Win",
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


def _stub_llm(monkeypatch, extraction=None, side_effect=None):
    structured_llm = MagicMock()
    if side_effect:
        structured_llm.invoke.side_effect = side_effect
    else:
        structured_llm.invoke.return_value = extraction
    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm
    monkeypatch.setattr(report_module, "ChatAnthropic", MagicMock(return_value=llm))
    return structured_llm


def _base_state(**overrides):
    state = {
        "business_name": "Acme Co",
        "description": "Widgets",
        "input_url": "https://example.com",
        "robots_txt": {"exists": True},
        "llms_txt": {"exists": False},
        "llms_full_txt": {"exists": False},
        "schema": {"exists": True, "schema_type": ["Organization"]},
        "prospect_visibility": {"total_prospect_score": 0},
        "competitor_visibility": {},
    }
    state.update(overrides)
    return state


def test_report_success_generates_pdf(monkeypatch):
    _stub_llm(monkeypatch, extraction=_extraction())
    monkeypatch.setattr(report_module, "generate_pdf", MagicMock(return_value="/tmp/report.pdf"))

    result = report(_base_state())

    assert result["overall_score"] == 5
    assert result["pdf_path"] == "/tmp/report.pdf"
    assert "errors" not in result


def test_report_retries_structured_output_on_validation_error(monkeypatch):
    extraction = _extraction()
    structured_llm = _stub_llm(monkeypatch, side_effect=[ValueError("missing quick_win"), extraction])
    monkeypatch.setattr(report_module, "generate_pdf", MagicMock(return_value="/tmp/report.pdf"))

    result = report(_base_state())

    assert structured_llm.invoke.call_count == 2
    assert result["overall_score"] == 5
    assert result["pdf_path"] == "/tmp/report.pdf"


def test_report_falls_back_to_initial_score_after_exhausting_retries(monkeypatch):
    _stub_llm(monkeypatch, side_effect=ValueError("missing quick_win"))

    result = report(_base_state())

    assert "errors" in result
    assert "overall_score" in result
    assert "pdf_path" not in result


def test_report_captures_pdf_generation_failure(monkeypatch):
    _stub_llm(monkeypatch, extraction=_extraction())
    monkeypatch.setattr(report_module, "generate_pdf", MagicMock(side_effect=RuntimeError("weasyprint failed")))

    result = report(_base_state())

    assert result["overall_score"] == 5
    assert "pdf_path" not in result
    assert "errors" in result
    assert "weasyprint failed" in result["errors"][0]
