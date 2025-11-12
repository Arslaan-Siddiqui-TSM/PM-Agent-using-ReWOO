"""
Feasibility Graph

Simple graph for feasibility assessment generation.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph, START

from src.states.feasibility_state import FeasibilityState


def _generate_assessment(state: FeasibilityState) -> dict:
    """Generate feasibility assessment (thinking + report)."""
    from src.app.feasibility_agent import generate_feasibility_questions
    
    print(f"Graph node: generate_assessment - Starting feasibility generation")
    
    result = generate_feasibility_questions(
        document_text="",  # Not used in v3 mode with md_file_paths
        development_context=state.development_context,
        session_id=state.session_id,
        md_file_paths=state.md_file_paths
    )
    
    print(f"Graph node: generate_assessment - Complete")
    
    return {
        "thinking_summary": result.get("thinking_summary", ""),
        "feasibility_report": result.get("feasibility_report", "")
    }


def get_feasibility_graph(state: FeasibilityState):
    """Build the feasibility assessment graph."""
    if not state:
        return None
    
    graph = StateGraph(FeasibilityState)
    
    graph.add_node("generate_assessment", _generate_assessment)
    
    graph.add_edge(START, "generate_assessment")
    graph.add_edge("generate_assessment", END)
    
    return graph.compile()
