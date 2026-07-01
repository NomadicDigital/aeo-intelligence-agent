from langgraph.graph import END, StateGraph

from graph import route_after_research
from state import AgentState


def _build_stub_graph(call_log):
    """
    Builds a graph with the real routing function but stub nodes, so the
    fan-out/fan-in topology can be asserted without touching any external API.
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

    g = StateGraph(AgentState)
    g.add_node("research", stub_research)
    g.add_node("technical_audit", stub_technical_audit)
    g.add_node("visibility_analysis", stub_visibility_analysis)
    g.add_node("report", stub_report)
    g.set_entry_point("research")
    g.add_conditional_edges(
        "research",
        route_after_research,
        ["technical_audit", "visibility_analysis", "report"],
    )
    g.add_edge("technical_audit", "report")
    g.add_edge("visibility_analysis", "report")
    g.add_edge("report", END)
    return g.compile()


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
