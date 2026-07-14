from state import AgentState
import logging
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

MAX_REPORT_ATTEMPTS = 3


class ReportOutput(BaseModel):
    overall_score: int = Field(description="Overall AEO score between 0-10 based on the provided initial_score. Do not deviate significantly from the initial_score provided.")
    key_improvements: str = Field(description="The top 3 key improvements the website can make to improve AEO, as a formatted string with each improvement on a new line.")
    high_level_summary: str = Field(description="1 concise paragraph giving a high level summary of the information in the report and the brand's overall performance")
    visibility_insight: str = Field(description="1 sentence comparing the prospect's visibility to the competitor's")
    quick_win: str = Field(description="Identify and concisely describe the single most impactful thing the client do today to improve AEO performance")

def generate_initial_score(llms_txt, llms_full_text, schema, robots_txt, prospect_visibility_score):
    """
    This function generates an initial score based on the outputs from the Technical Audit & Visbility analysis
    agents
    """
    prospect_initial_score = 0
    if llms_txt or llms_full_text:
        prospect_initial_score+=1
    if schema:
        prospect_initial_score+=3
    if robots_txt:
        prospect_initial_score+=2
    visbility_optimisation_score = (prospect_visibility_score / 100)*4
    prospect_initial_score += visbility_optimisation_score
    return round(prospect_initial_score)


def invoke_structured_report_with_retry(structured_llm, messages, max_attempts=MAX_REPORT_ATTEMPTS):
    """
    Claude occasionally omits a required field (e.g. quick_win) from the
    structured report output, which raises a pydantic validation error.
    Retry a few times before giving up.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return structured_llm.invoke(messages)
        except Exception as e:
            last_error = e
            logger.warning("Structured report extraction attempt %d/%d failed: %s", attempt, max_attempts, e)
    raise last_error

def report(state:AgentState) -> AgentState:
    """
    Main report node of the Agentic model. It takes the inputs from the other 3 nodes, generating an overall report
    to be used to support AEO lead generation
    """
    
    errors = []

    # Step 1: Generate initial score
    initial_score = generate_initial_score(
        state.get('llms_txt', {}).get('exists', False),
        state.get('llms_full_txt', {}).get('exists', False),
        state.get('schema', {}).get('exists', False),
        state.get('robots_txt', {}).get('exists', False),
        state.get('prospect_visibility', {}).get('total_prospect_score', 0)
    )

    try:
        llm = ChatAnthropic(model="claude-sonnet-5", max_tokens=4000)
        structured_llm = llm.with_structured_output(ReportOutput)
        system_prompt = (
                """
                You're an AEO (Answer Engine Optimisation) expert, synthesising data in an AEO (Answer Engine Optimisation) project. 
                You have been passed numerous data points about a prospect's business, website and current AEO visibility. I've also included information about their competitor's performance. 
                Please analyse the data and produce a report based on the prospect's current optimisation levels and potential improvements.
                """
            )
        
        user_prompt = f"""
        Here is the data for your analysis:

        **Business:** {state['business_name']}
        **Description:** {state['description']}

        **Robots.txt:** Exists: {state['robots_txt'].get('exists')} | Blocked crawlers: {state['robots_txt'].get('blocked_ai_crawlers', [])}
        **LLMs.txt:** Exists: {state['llms_txt'].get('exists')}
        **LLMs-full.txt:** Exists: {state['llms_full_txt'].get('exists')}
        **Schema:** Exists: {state['schema'].get('exists')} | Types found: {state['schema'].get('schema_type', [])}

        **Prospect's visibility:** {state['prospect_visibility']}
        **Competitor visibility:** {state['competitor_visibility']}

        **Calculated Initial Score:** {initial_score}/10

        Please generate the report based on this data.
        """
        
        logger.info("Passing context data into structured Claude model")
        extraction: ReportOutput = invoke_structured_report_with_retry(structured_llm, [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        logger.info("Report extraction successful: overall_score=%s", extraction.overall_score)
        logger.debug(
            "Report fields: key_improvements=%s high_level_summary=%s visibility_insight=%s quick_win=%s",
            extraction.key_improvements,
            extraction.high_level_summary,
            extraction.visibility_insight,
            extraction.quick_win,
        )

        result = {
            "overall_score": extraction.overall_score,
            "high_level_summary": extraction.high_level_summary,
            "key_improvements": extraction.key_improvements,
            "visibility_insight": extraction.visibility_insight,
            "quick_win": extraction.quick_win,
        }

        try:
            pdf_path = generate_pdf(
                business_name=state["business_name"],
                input_url=state["input_url"],
                overall_score=extraction.overall_score,
                high_level_summary=extraction.high_level_summary,
                key_improvements=extraction.key_improvements,
                visibility_insight=extraction.visibility_insight,
                quick_win=extraction.quick_win,
                robots_txt=state.get("robots_txt", {}),
                llms_txt=state.get("llms_txt", {}),
                llms_full_txt=state.get("llms_full_txt", {}),
                schema=state.get("schema", {}),
                prospect_visibility=state.get("prospect_visibility", {}),
                competitor_visibility=state.get("competitor_visibility", {}),
            )
            logger.info("PDF saved to: %s", pdf_path)
            result["pdf_path"] = pdf_path
        except Exception as e:
            logger.error("PDF generation failed: %s", e)
            result["errors"] = [f"PDF generation failed: {str(e)}"]

        return result
        

    except Exception as e:
        error_msg = f"Report LLM response failed: {str(e)}"
        logger.error(error_msg)
        return {
            "overall_score": initial_score,
            "errors": [error_msg]
        }