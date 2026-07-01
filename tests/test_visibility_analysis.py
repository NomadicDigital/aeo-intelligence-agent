from unittest.mock import MagicMock

from agents import visibility_analysis as visibility_module
from agents.visibility_analysis import visibility_analysis


def _stub_llm(monkeypatch, responses=None, side_effect=None):
    llm = MagicMock()
    if side_effect:
        llm.invoke.side_effect = side_effect
    else:
        llm.invoke.side_effect = [MagicMock(content=r) for r in responses]
    monkeypatch.setattr(visibility_module, "ChatAnthropic", MagicMock(return_value=llm))
    return llm


def test_visibility_analysis_scores_prospect_and_competitor_mentions(monkeypatch):
    _stub_llm(monkeypatch, responses=[
        "Acme Co is a great choice for widgets.",
        "Widget Corp is the market leader.",
    ])

    state = {
        "business_name": "Acme Co",
        "competitors": ["Widget Corp"],
        "core_queries": ["best widget maker", "leading widget company"],
    }

    result = visibility_analysis(state)

    assert result["prospect_visibility"]["total_prospect_score"] == 50.0
    assert result["prospect_visibility"]["query_breakdown"] == {
        "best widget maker": 1,
        "leading widget company": 0,
    }
    assert result["competitor_visibility"]["Widget Corp"] == 50.0
    assert "errors" not in result


def test_visibility_analysis_handles_llm_errors_per_query(monkeypatch):
    _stub_llm(monkeypatch, side_effect=RuntimeError("rate limited"))

    state = {
        "business_name": "Acme Co",
        "competitors": ["Widget Corp"],
        "core_queries": ["best widget maker"],
    }

    result = visibility_analysis(state)

    assert result["prospect_visibility"]["total_prospect_score"] == 0
    assert "errors" in result
    assert "rate limited" in result["errors"][0]


def test_visibility_analysis_handles_no_queries():
    state = {
        "business_name": "Acme Co",
        "competitors": ["Widget Corp"],
        "core_queries": [],
    }

    result = visibility_analysis(state)

    assert result["prospect_visibility"]["total_prospect_score"] == 0
    assert result["competitor_visibility"] == {"Widget Corp": 0}
