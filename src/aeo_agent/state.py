from typing import TypedDict, List, Dict, Any, Annotated
import operator

class AgentState(TypedDict):
    # Input
    url: str
    email: str

    # System State

    errors: Annotated[List[str], operator.add]

    # Research
    business_name: str
    description: str
    competitors: List[str]
    core_queries: List[str]

    # Technical Audit
    llms_txt: Dict[str, Any]
    llms_full_txt: Dict[str, Any]
    robots_txt: Dict[str, Any]
    schema: Dict[str, Any]

    # Visibility agent
    prospect_visibility: Dict[str, int]
    competitor_visibility: Dict[str, Dict[str, int]]

    # Report Agent
    overall_score: int
    high_level_summary: str
    pdf_path: str

