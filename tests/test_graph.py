from graph import build_graph


def _build_stub_graph(call_log):
    """
    Builds the real graph from graph.py with stub nodes, so the fan-out/fan-in
    topology can be asserted without touching any external API.
    """
    def stub_research(state):
        call_log.append("research")
        return {}

    def stub_technical_audit(state):
        call_log.append("technical_audit")
        return {"schema": {"exists": True}}

    def stub_visibility_analysis(state):
        call_log.append("visibility_analysis")
        return {"prospect_visibility": {"total_prospect_score": 10}}

    def stub_report(state):
        call_log.append("report")
        return {"overall_score": 5}

    return build_graph(
        research_node=stub_research,
        technical_audit_node=stub_technical_audit,
        visibility_analysis_node=stub_visibility_analysis,
        report_node=stub_report,
    )


def _base_state(**overrides):
    state = {
        "input_url": "https://example.com",
        "email": "",
        "errors": [],
        "business_name": "Acme Co",
        "description": "Widgets",
        "competitors": ["Widget Corp"],
        "core_queries": ["best widget maker"],
        "raw_html": "<html></html>",
        "llms_txt": {},
        "llms_full_txt": {},
        "robots_txt": {},
        "schema": {},
        "prospect_visibility": {},
        "competitor_visibility": {},
        "overall_score": 0,
        "high_level_summary": "",
        "key_improvements": [],
        "visibility_insight": "",
        "quick_win": "",
        "pdf_path": "",
    }
    state.update(overrides)
    return state


def test_successful_research_fans_out_to_both_analysis_nodes_and_joins_once():
    call_log = []
    app = _build_stub_graph(call_log)

    app.invoke(_base_state())

    assert call_log.count("technical_audit") == 1
    assert call_log.count("visibility_analysis") == 1
    assert call_log.count("report") == 1
    assert call_log[-1] == "report"


def test_failed_research_skips_straight_to_report():
    call_log = []
    app = _build_stub_graph(call_log)

    app.invoke(_base_state(business_name=""))

    assert "technical_audit" not in call_log
    assert "visibility_analysis" not in call_log
    assert call_log.count("report") == 1
