from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph, START

from app.draft import generate_draft
from app.reflect import generate_reflection
from app.revise import apply_revision
from states.reflection_state import ReflectionState


def _route_after_revision(state: ReflectionState) -> Literal["draft", "finalize"]:
    if state.final_plan is not None:
        return "finalize"
    return "draft"


def _finalize_node(state: ReflectionState) -> dict:
    if state.final_plan is None and state.current_draft is not None:
        # Safeguard: if we reach finalize without explicitly setting final_plan,
        # return the latest draft as the final result.
        return {"final_plan": state.current_draft}
    return {}


def get_graph(state: ReflectionState):
    """Build the reflection-style reasoning graph."""

    if not state:
        return None

    graph = StateGraph(ReflectionState)

    graph.add_node("draft", generate_draft)
    graph.add_node("reflect", generate_reflection)
    graph.add_node("revise", apply_revision)
    graph.add_node("finalize", _finalize_node)

    graph.add_edge(START, "draft")
    graph.add_edge("draft", "reflect")
    graph.add_edge("reflect", "revise")
    graph.add_conditional_edges("revise", _route_after_revision)
    graph.add_edge("finalize", END)

    return graph.compile()
