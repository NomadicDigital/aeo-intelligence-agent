from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END
import random

class AgentState(TypedDict):
    player_name: str
    guesses: List[int]
    attempts: int
    lower_bound: int
    upper_bound: int
    target_number: int

def setup(state: AgentState) -> AgentState:
    """This function sets up the game"""
    state['attempts'] = 0
    state['target_number'] = random.randint(state['lower_bound'], state['upper_bound'])
    return state

def guess(state: AgentState) -> AgentState:
    """This function makes a guess"""
    if len(state['guesses']) > 0:
        last_guess = state['guesses'][-1]
        if last_guess > state['target_number']:
            state['upper_bound'] = last_guess - 1
        elif last_guess < state['target_number']:
            state['lower_bound'] = last_guess + 1
    current_guess = random.randint(state['lower_bound'], state['upper_bound'])
    state['guesses'].append(current_guess)
    state['attempts'] += 1
    return state

def hint_node(state: AgentState) -> AgentState:
    """This function gives a hint about whether it's higher or lower"""
    last_guess = state['guesses'][-1] 
    if(last_guess == state['target_number']) or (state['attempts'] == 7):
        return "exit"
    else:
         return "continue"

graph = StateGraph(AgentState)

graph.add_node("setup", setup)
graph.add_node("guess", guess)

graph.set_entry_point("setup")
graph.add_edge("setup", "guess")

graph.add_conditional_edges(
    "guess",
    hint_node,
    {
        "exit": END,
        "continue": "guess"
    }
)

app = graph.compile()

print(app.invoke({"player_name": "Student", "guesses": [], "attempts": 0, "lower_bound": 1, "upper_bound": 5}))