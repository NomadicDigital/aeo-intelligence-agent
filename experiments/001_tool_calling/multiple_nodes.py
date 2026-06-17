from typing import List, TypedDict
from langgraph.graph import StateGraph
import math

class AgentState(TypedDict):
    name: str
    age: str
    skills: List[str]
    result: str

def first_node(state: AgentState) -> AgentState:
    """ First Node that processes the name """

    state['result'] = f"{state['name']}, welcome to the system!"
    return state

def second_node(state: AgentState) -> AgentState:
    """ Second Node that processes the age """

    state['result'] = state['result']+ f" You are {state['age']} years old!"
    return state

def third_node(state: AgentState) -> AgentState:
    """ Final Node that processing the list of user skills """
    skills_str = "".join(state['skills'])
    state['result'] = state['result'] + f"You have skills in {str(skills_str)}"
    return state

graph = StateGraph(AgentState)

graph.add_node("first_node", first_node)
graph.add_node("second_node", second_node)
graph.add_node("third_node", third_node)
graph.set_entry_point("first_node")
graph.add_edge('first_node', 'second_node')
graph.add_edge('second_node', 'third_node')
graph.set_finish_point("third_node")

app = graph.compile()

answers = app.invoke({"name": "Jack Sparrow", 'age': "16", "skills": ['Hiking', 'Skiing', 'Jogging']})
print(answers)