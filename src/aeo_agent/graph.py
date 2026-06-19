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

def route_after_research(state:AgentState) -> str:
    """
    This function verifies if the research bot has been successfull or encountered
    errors and decides the route based on that. 
    """
    business_name = state["business_name"]
    description = state["description"]
    competitors = state["competitors"]
    core_queries = state["core_queries"]
    if not (business_name) and not (description) and not (competitors) and not core_queries:
        return "skip"
    else:
         return "continue"

# --------------------------------------------------
# Stage 3: Parallel Analysis
# --------------------------------------------------

# Run Technical Audit and Visibility Analysis
# in parallel using conditional edge and standard graph edge

graph.add_conditional_edges(
    "research",
    route_after_research,
    {
        "continue": "technical_audit",
        "skip": "report"
    }
)

graph.add_edge("research", "visibility_analysis")


# --------------------------------------------------
# Stage 4: Fan-In / Report Generation
# --------------------------------------------------

# Wait for both parallel branches to complete

graph.add_edge("technical_audit", "report")
graph.add_edge("visibility_analysis", "report")


# --------------------------------------------------
# Stage 5: End
# --------------------------------------------------

graph.add_edge("report", END)
app = graph.compile()