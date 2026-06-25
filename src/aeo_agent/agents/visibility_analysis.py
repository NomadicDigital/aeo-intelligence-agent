from state import AgentState
from langchain_anthropic import ChatAnthropic

def visibility_analysis(state:AgentState) -> AgentState:
    prospect_mentions = 0
    query_breakdown = {}
    competitor_mentions = {comp: 0 for comp in state['competitors']}
    errors = []
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    for query in state['core_queries']:
        try:
            print(f"Query being passed is {query}")
            response = llm.invoke([{"role": "user", "content": query}])
            print(f"Respone {response.content}")
            if state['business_name'].lower() in response.content.lower():
                query_breakdown[query] = 1
                prospect_mentions+=1 
            else:
                query_breakdown[query] = 0
            for competitor in state['competitors']:
                if competitor.lower() in response.content.lower():
                    competitor_mentions[competitor] +=1

        except Exception as e:
            error_msg = f"LLM response failed for query: {query}: {str(e)}"
            query_breakdown[query] = 0  
            errors.append(error_msg)

    if state['core_queries']:
        total_prospect_visibility = (prospect_mentions / len(state['core_queries'])) * 100
        total_competitor_visibility = {
            comp: (mentions / len(state['core_queries'])) * 100 
            for comp, mentions in competitor_mentions.items()
        }
    else:
        total_prospect_visibility = 0
        total_competitor_visibility = {comp: 0 for comp in competitor_mentions}
        
    final_update = {
        "prospect_visibility": {
            "total_prospect_score": total_prospect_visibility,
            "query_breakdown": query_breakdown
            },
        "competitor_visibility": total_competitor_visibility
        }
    
    if errors:
        final_update['errors'] = errors

    return final_update