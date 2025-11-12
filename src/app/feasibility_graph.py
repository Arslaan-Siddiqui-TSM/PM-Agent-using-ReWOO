"""
Feasibility Graph

Simple graph for feasibility assessment generation.
"""

from __future__ import annotations
from pathlib import Path

from langgraph.graph import END, StateGraph, START

from src.states.feasibility_state import FeasibilityState


def _read_md_files(md_file_paths: list[str]) -> str:
    """Read and combine all MD files into a unified context document.
    
    Args:
        md_file_paths: List of absolute paths to markdown files
        
    Returns:
        Combined markdown content with document separators
    """
    if not md_file_paths:
        print("Warning: No MD file paths provided")
        return ""
    
    print(f"Reading {len(md_file_paths)} MD files for unified context...")
    md_content = []
    
    for md_path_str in md_file_paths:
        md_path = Path(md_path_str)
        if md_path.exists():
            print(f"  Reading: {md_path.name}")
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Add document header for clarity
                doc_name = md_path.stem
                md_content.append(f"# Document: {doc_name}\n\n{content}")
                print(f"    Loaded {len(content)} characters")
        else:
            print(f"  Warning: MD file not found: {md_path}")
    
    if not md_content:
        print("Warning: No MD files could be read")
        return ""
    
    # Combine with separators
    unified_context = "\n\n---\n\n".join(md_content)
    print(f"Combined unified context: {len(unified_context)} characters from {len(md_content)} files")
    
    return unified_context


def _generate_assessment(state: FeasibilityState) -> dict:
    """Generate feasibility assessment (thinking + report)."""
    from src.app.feasibility_agent import generate_feasibility_questions
    
    print(f"Graph node: generate_assessment - Starting feasibility generation")
    
    # Read and combine all MD files into unified context
    document_text = _read_md_files(state.md_file_paths or [])
    
    result = generate_feasibility_questions(
        document_text=document_text,
        development_context=state.development_context,
        session_id=state.session_id
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
