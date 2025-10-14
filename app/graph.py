from langgraph.graph import END, StateGraph, START
from app.plan import get_plan
from app.tool_executor import tool_execution
from utils.helper import route
from states.rewoo_state import ReWOO
from app.solver import solve

def get_graph(state: ReWOO):
    """
    Initializes and compiles the LangGraph for the agent. If no state is provided, returns None.
    Otherwise, sets up the nodes and edges of the graph based on the provided state.

    Args:
        state (ReWOO): The current state of the ReWOO agent.
    Returns:
        StateGraph | None: The compiled StateGraph if state is provided, else None.
    """

    if not state:
        return None
    else:
        graph = StateGraph(ReWOO)

        graph.add_node("plan", get_plan)
        graph.add_node("tool", tool_execution)
        graph.add_node("solve", solve)

        graph.add_edge("plan", "tool")
        graph.add_edge("solve", END)
        graph.add_conditional_edges("tool", route)
        graph.add_edge(START, "plan")

        return graph.compile()
