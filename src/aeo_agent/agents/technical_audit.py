from state import AgentState
from typing import Dict
import requests

AI_CRAWLERS = ["GPTBot", "ClaudeBot", "Google-Extended", "PerplexityBot", "OAI-SearchBot"]

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
    robots_url = f"{input_url}/robots.txt"
    blocked_crawlers, allowed_crawlers, unmentioned_crawlers = [],[],[]
    
    # Step 1: Fetch robots.txt
    r = requests.get(robots_url)

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
    if r.status_code == 200:
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

def technical_audit(state:AgentState) -> AgentState:
    return {}