from langgraph.graph import END, StateGraph, START
from states.rewoo_state import ReWOO
from app.plan import get_plan
from app.tool_executor import tool_execution
from app.solver import solve
from utils.helper import route


def get_graph(state: ReWOO):
    """
    Initializes the ReWOO agent graph for planning.
    Assumes feasibility questions have been answered in a single markdown file.
    """
    if not state:
        return None

    graph = StateGraph(ReWOO)

    # Planning node
    graph.add_node("plan", get_plan)
    # Tool execution node
    graph.add_node("tool", tool_execution)
    # Solver node
    graph.add_node("solve", solve)

    # Graph edges
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "tool")
    graph.add_conditional_edges("tool", route)
    graph.add_edge("solve", END)

    return graph.compile()
