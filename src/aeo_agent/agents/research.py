from state import AgentState
import os
from dotenv import load_dotenv
from firecrawl import Firecrawl
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import time
import random
from langchain_anthropic import ChatAnthropic

load_dotenv()

crawler_api_key = os.getenv("FIRECRAWL_API_KEY")
crawler_app = Firecrawl(api_key=crawler_api_key)
RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}

class ResearchExtraction(BaseModel):
    business_name: str = Field(description="The formal or highly recognizable name of the business.")
    description: str = Field(description="A 2-3 sentence summary of what the business does, their target market, and value proposition.")
    competitors: List[str] = Field(description="Identify 3-5 key competitors in their space based on the scraped content.")
    core_queries: List[str] = Field(description="List 5-8 conversational search queries prospects would use to find this service on LLMS. Do not mention the brand, instead let it be non-branded queries. (e.g., 'What is the best custom software agency in London?')")

def request_with_retry(url, max_attempts=5):
    """
    Scrapes the URL using FirecrawlApp with custom exponential backoff, retry limits,
    and jitter to safely bypass rate limits and transient server failures.
    """
    for attempt in range(max_attempts):
        resp = crawler_app.scrape(url, formats=['markdown', 'rawHtml'])
        if resp.metadata.status_code < 400 or resp.metadata.status_code not in RETRYABLE_STATUSES:
            return resp
        retry_after = resp.headers.get("Retry-After")
        delay = float(retry_after) if retry_after else min(2 ** attempt, 30) + random.random()
        time.sleep(delay)
    return resp

def scrape_url(url) -> str:
    """
    Orchestrates the scraping action and classifies errors into system exceptions
    vs. operational state errors as per system design.
    """
    data = crawler_app.scrape(url, formats=['markdown', "rawHtml"])
    status_code = data.metadata.status_code
    print(f"RAW_HTML: {data.raw_html}")
    if status_code == 200:
        return data
    elif status_code in {401, 402}:
        raise Exception(f"System error. The crawler returned a status code of {status_code}")
    # Operational failures (403, 404) → append to errors, return state
    elif status_code in {403, 404}:
        return None
    elif status_code in RETRYABLE_STATUSES:
        data = request_with_retry(url)
        if data.metadata.status_code == 200:
            return data
        else:
            return None


def research(state:AgentState) -> AgentState:
    """
    The main Research Node in our LangGraph execution.
    Analyses the target website, runs structured extraction, and returns state updates.
    """
    print(f"\n--- 🕵️‍♂️ Starting Research Node for {state['input_url']} ---")
    # Initialise Firecrawl and scrape the URL
    data = scrape_url(state['input_url'])
    print(f"Scraped data received.")
    # PATH 1: Scrape Failed
    if data is None:
        error_msg = f"Could not scrape {state['input_url']}"
        print(f"❌ {error_msg}")
        return {"errors": [error_msg]}
    
    #PATH 2: Scrape succeeded, pass to LLM
    try:
        llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
        structured_llm = llm.with_structured_output(ResearchExtraction)
        system_prompt = (
                """
                You're an leading market research assistant, acting as the main researcher in an AEO (Answer Engine Optimisation) project. 
                You have been passed a raw markdown file from a Firecrawl scrape. Please analyse the content and extract key business details. 
                Use your internal knowledge base to identify competitors if the the scraped text doesn't list them explicitly
                """
            )
        
        user_prompt = (
            f"Here is some scraped data from the website:\n\n"
            f"Website title: {data.metadata.title}\n"
            f"Description: {data.metadata.description}\n\n"
            f"Content:\n{data.markdown[:20000]}"
        )
        
        print("🧠 Parsing scraped content with structured Claude model...")
        print(f"Data being passed is {data.markdown[:2000]}")
        extraction: ResearchExtraction = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        print("✅ Extraction successful!")

        print("Business:", extraction.business_name)
        print("Description:", extraction.description)
        print("Competitors:", extraction.competitors)
        print("Queries:", extraction.core_queries)
        
        return {
            "business_name": extraction.business_name,
            "description": extraction.description,
            "competitors": extraction.competitors,
            "core_queries": extraction.core_queries,
            "raw_html": data.raw_html
        }
    
    except Exception as e:
        error_msg = f"LLM response failed for {state['input_url']}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"errors": [error_msg]} 