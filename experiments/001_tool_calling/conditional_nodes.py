from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    number1: int
    number2: int
    operation: str
    finalNumber: int
    number3: int
    number4: int
    operation2: str
    finalNumber2: int

def add_node(state: AgentState) -> AgentState:
    """Fn to add two numbers"""
    state['finalNumber'] = state['number1'] + state['number2']
    return state

def sub_node(state: AgentState) -> AgentState:
    """Fn to add two numbers"""
    state['finalNumber'] = state['number1'] - state['number2']
    return state

def add_node2(state: AgentState) -> AgentState:
    """Fn to add two numbers"""
    state['finalNumber2'] = state['number3'] + state['number4']
    return state

def sub_node2(state: AgentState) -> AgentState:
    """Fn to add two numbers"""
    state['finalNumber2'] = state['number3'] - state['number4']
    return state

def router(state:AgentState) -> str:
    """Decide first router"""
    if state['operation'] == '+':
        return "addition_operation"
    if state['operation'] == '-':
        return "sub_operation"

def router2(state:AgentState) -> str:
    """Decide second router"""
    if state['operation2'] == '+':
        return "addition_operation2"
    if state['operation2'] == '-':
        return "sub_operation2"

graph = StateGraph(AgentState)
graph.add_node("add_node", add_node)
graph.add_node("sub_node", sub_node)
graph.add_node("router", lambda state:state)

graph.add_node("add_node2", add_node2)
graph.add_node("sub_node2", sub_node2)
graph.add_node("router2", lambda state:state)

graph.add_edge(START, "router")
graph.add_conditional_edges(
    "router",
    router,
    {
        "addition_operation": "add_node",
        "sub_operation": "sub_node"
    }
)
graph.add_edge("add_node", "router2")
graph.add_edge("sub_node", "router2")
graph.add_conditional_edges(
    "router2",
    router2,
    {
        "addition_operation2": "add_node2",
        "sub_operation2": "sub_node2"
    }
)

graph.add_edge("add_node2", END)
graph.add_edge("sub_node2", END)

app = graph.compile()

initial_state_1 = AgentState(number1 = 10, number2=5, operation="+", number3= 20, number4=10, operation2="-")
print(app.invoke(initial_state_1))