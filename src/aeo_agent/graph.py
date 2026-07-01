from typing import List

from state import AgentState
from langgraph.graph import StateGraph, END
from agents.research import research
from agents.technical_audit import technical_audit
from agents.visibility_analysis import visibility_analysis
from agents.report import report

# Define AgentState schema

graph = StateGraph(AgentState)

# --------------------------------------------------
# Nodes
# --------------------------------------------------

graph.add_node('research', research)
graph.add_node('technical_audit', technical_audit)
graph.add_node('visibility_analysis', visibility_analysis)
graph.add_node('report', report)

# --------------------------------------------------
# Stage 1: Entry Point
# --------------------------------------------------

graph.set_entry_point('research')

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

# Wait for both parallel branches to complete before generating the report
graph.add_edge("technical_audit", "report")
graph.add_edge("visibility_analysis", "report")


# --------------------------------------------------
# Stage 5: End
# --------------------------------------------------

graph.add_edge("report", END)
app = graph.compile()