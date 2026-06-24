from state import AgentState
from typing import Dict
import requests
from bs4 import BeautifulSoup
import json

AI_CRAWLERS = ["GPTBot", "ClaudeBot", "Google-Extended", "PerplexityBot", "OAI-SearchBot"]
TIMEOUT_TIME = 10
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def find_robot_rule(agent, robots_txt_contents) -> str:
    """
    Function for finding the current rule (Allow or Disallow) for a user_agent in a 
    Robots.txt files contents. Returning the string.
    """
    user_agent = f"User-agent: {agent}"
    start = robots_txt_contents.find(f"{user_agent}")
    if start == -1:
        return "Unknown"
    else:
        section = robots_txt_contents[start:]
        lines = section.split('\n')
        rule = lines[1]
        if "Allow" in rule:
            return "Allow"
        elif "Disallow" in rule:
            return "Disallow"
        else:
            return "Unknown"


def check_robots_txt(input_url) -> Dict:
    """
    Function for checking the website's Robots.txt file for initial existance. If it exists, 
    we store the raw contents and then check for any explicit rules for LLMBots.
    """
    clean_url = input_url.rstrip('/')
    robots_url = f"{clean_url}/robots.txt"
    blocked_crawlers, allowed_crawlers, unmentioned_crawlers = [],[],[]
    
    # Step 1: Fetch robots.txt
    try:
        r = requests.get(robots_url, timeout=TIMEOUT_TIME, headers=HEADERS)
    except requests.exceptions.Timeout:
        error_msg = f"Robots timed out"
        return {
            "robots_txt": {
                "exists": False
            },
            "errors": [error_msg]
        }

    # Step 2: Handle failure cases
    if r.status_code == 404:
        return {
            "robots_txt": {
                "exists": False
            }
        }
    
    elif r.status_code != 200:
        error_msg = f"Robots response failed for with status code: {r.status_code}"
        print(f"❌ {error_msg}")
        return {
            "robots_txt": {
                "exists": False
            },
            "errors": [error_msg]
        }

    # Step 3: If exists, check each AI crawler
    robots_txt_contents = r.text
    for crawler in AI_CRAWLERS:
        if f"User-agent: {crawler}" in robots_txt_contents:
            rule = find_robot_rule(crawler, robots_txt_contents)
            if rule == 'Allow':
                allowed_crawlers.append(crawler)
            elif rule == 'Disallow':
                blocked_crawlers.append(crawler)
            else:
                unmentioned_crawlers.append(crawler)
        elif "User-agent: *" in robots_txt_contents:
                rule = find_robot_rule("*", robots_txt_contents)
                if rule == 'Allow':
                    allowed_crawlers.append(crawler)
                elif rule == 'Disallow':
                    blocked_crawlers.append(crawler)
        else:
            unmentioned_crawlers.append(crawler)
    return {
        "robots_txt": {
            "exists": True,
            "raw_content": robots_txt_contents,
            "blocked_ai_crawlers": blocked_crawlers,
            "allowed_ai_crawlers": allowed_crawlers,
            "unmentioned_ai_crawlers": unmentioned_crawlers
        }
    }
    
def check_llm_files(input_url, file_name, state_key):
    """
    Function for checking the website's LLMs.txt and LLMS-full file for initial existance. If it exists, 
    we store the raw contents.
    """
    clean_url = input_url.rstrip('/')
    llm_file_url = f"{clean_url}/{file_name}"
    # Step 1: Fetch file
    try:
        r = requests.get(llm_file_url, timeout=TIMEOUT_TIME)
    except requests.exceptions.Timeout:
        error_msg = f"{file_name} timed out"
        return {
            f"{state_key}": {
                "exists": False
            },
            "errors": [error_msg]
        }
    
    # Step 2: Handle failure cases
    if r.status_code == 404:
        return {
            f"{state_key}": {
                "exists": False
            }
        }
    
    elif r.status_code != 200:
        error_msg = f"{file_name} response failed for with status code: {r.status_code}"
        print(f"❌ {error_msg}")
        return {
            f"{state_key}": {
                "exists": False
            },
            "errors": [error_msg]
        }
    
    file_contents = r.text
    return {
        f"{state_key}":
        {
            "exists": True,
            "raw_content": file_contents
            }
        }

def check_for_schema(raw_html) -> Dict:
    """
    Function for checking the website's RAW Html output for Schema. If it exists, 
    we store the types in the state.
    """
    # Step 1: Parse HTML with BeautifulSoup
    parsed_html = BeautifulSoup(raw_html, "html.parser")
    schemas = parsed_html.find_all('script', type='application/ld+json')
    found_schemas = []
    for schema in schemas:
        try:
            data = json.loads(schema.string)
            # Handle both single objects and arrays of schema objects
            if isinstance(data, dict):
                schema_type = data.get('@type')
                if schema_type:
                    found_schemas.append(schema_type)
            elif isinstance(data, list):
                for item in data:
                    schema_type = item.get('@type')
                    if schema_type:
                        found_schemas.append(schema_type)
        except (json.JSONDecodeError, AttributeError):
            continue
    if found_schemas:
        return {
            "schema": 
            {
                "exists": True,
                "schema_type": found_schemas
            }
        }
    else:
        return {
            "schema":
            {
                "exists": False
            }
        }
    
def strip_errors(d):
    """
    Helper function to remove any 'errors' from the other states.
    """
    return {k: v for k, v in d.items() if k != "errors"}

def technical_audit(state:AgentState) -> AgentState:
    """
    The main Technical Node in our LangGraph execution.
    Extracts key data including robots.txt, llms-txt and Schema to provide as a key input to measure a 
    website's overall AEO optimisations levels.
    """
    extracted_robots_txt = check_robots_txt(state['input_url'])
    extracted_llms_txt = check_llm_files(state['input_url'], 'llms.txt', 'llms_txt')
    extracted_llms_full_txt = check_llm_files(state['input_url'], 'llms-full.txt', 'llms_full_txt')
    extracted_schema = check_for_schema(state['raw_html'])
    errors = []
    for result in [extracted_robots_txt, extracted_llms_txt, extracted_llms_full_txt, extracted_schema]:
        if "errors" in result:
            errors.extend(result["errors"])
    final_update = {
        **strip_errors(extracted_robots_txt),
        **strip_errors(extracted_llms_txt),
        **strip_errors(extracted_llms_full_txt),
        **strip_errors(extracted_schema),
    }
    print(final_update)
    if errors:
        final_update["errors"] = errors
    return final_update