from typing import List

from state import AgentState
from langgraph.graph import StateGraph, END
from agents.research import research
from agents.technical_audit import technical_audit
from agents.visibility_analysis import visibility_analysis
from agents.report import report

# --------------------------------------------------
# Stage 2: Research Validation
# --------------------------------------------------

def route_after_research(state:AgentState) -> List[str]:
    """
    This function verifies if the research bot has been successfull or encountered
    errors and decides the route based on that. On success it fans out to both
    analysis nodes so they run in the same parallel step; on failure it skips
    straight to the Report node.
    """
    business_name = state["business_name"]
    description = state["description"]
    competitors = state["competitors"]
    core_queries = state["core_queries"]
    if not (business_name) or not (description) or not (competitors) or not core_queries:
        return ["report"]
    else:
        return ["technical_audit", "visibility_analysis"]


def build_graph(
    research_node=research,
    technical_audit_node=technical_audit,
    visibility_analysis_node=visibility_analysis,
    report_node=report,
):
    """
    Wires up and compiles the pipeline. The node functions are parameters so
    tests can run the real topology with stub nodes and no external API calls.
    """
    graph = StateGraph(AgentState)

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------

    graph.add_node('research', research_node)
    graph.add_node('technical_audit', technical_audit_node)
    graph.add_node('visibility_analysis', visibility_analysis_node)
    graph.add_node('report', report_node)

    # --------------------------------------------------
    # Stage 1: Entry Point
    # --------------------------------------------------

    graph.set_entry_point('research')

    # --------------------------------------------------
    # Stage 3: Parallel Analysis
    # --------------------------------------------------

    # Run Technical Audit and Visibility Analysis
    # in parallel by fanning out from research to both nodes

    graph.add_conditional_edges(
        "research",
        route_after_research,
        ["technical_audit", "visibility_analysis", "report"]
    )

    # --------------------------------------------------
    # Stage 4: Fan-In / Report Generation
    # --------------------------------------------------

    # Wait for both parallel branches to complete before generating the report.
    # A list of start nodes creates an explicit join, so report still runs once
    # even if one branch grows to more than one node.
    graph.add_edge(["technical_audit", "visibility_analysis"], "report")

    # --------------------------------------------------
    # Stage 5: End
    # --------------------------------------------------

    graph.add_edge("report", END)
    return graph.compile()


app = build_graph()
