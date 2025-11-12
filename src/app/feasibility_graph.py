"""
Feasibility Graph

Simple graph for feasibility assessment generation.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any

from langgraph.graph import END, StateGraph, START

from src.states.feasibility_state import FeasibilityState


def _create_unified_context_file(md_file_paths: list[str], session_id: str) -> Dict[str, Any]:
    """
    Create a unified context file containing all parsed documents.
    
    Args:
        md_file_paths: List of paths to markdown files (parsed documents)
        session_id: Session ID for the assessment
        
    Returns:
        dict: {
            "file_path": str,
            "total_chars": int,
            "documents_processed": int,
            "documents_failed": int
        }
    """
    print(f"\n{'='*60}")
    print(f"Creating unified context file for session {session_id[:8]}")
    print(f"Number of MD files to process: {len(md_file_paths)}")
    print(f"{'='*60}\n")
    
    # Create output directory
    output_dir = Path(f"output/session_{session_id[:8]}/context")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unified context file path
    unified_file_path = output_dir / f"unified_context_{session_id[:8]}.md"
    
    # Read and combine all MD files
    unified_content = []
    documents_processed = 0
    documents_failed = 0
    
    unified_content.append("# UNIFIED CONTEXT FILE")
    unified_content.append(f"Session ID: {session_id}\n")
    unified_content.append("---\n")
    
    # Add document content section
    unified_content.append("## PARSED DOCUMENTS\n")
    
    for idx, md_path_str in enumerate(md_file_paths, 1):
        md_path = Path(md_path_str)
        
        if not md_path.exists():
            print(f"⚠️  WARNING [{idx}/{len(md_file_paths)}]: File not found: {md_path}")
            documents_failed += 1
            continue
            
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"⚠️  WARNING [{idx}/{len(md_file_paths)}]: File is empty: {md_path.name}")
                documents_failed += 1
                continue
            
            # Add document header
            doc_name = md_path.name
            unified_content.append(f"\n### Document: {doc_name}\n")
            unified_content.append(content)
            unified_content.append("\n---\n")
            
            documents_processed += 1
            print(f"✅ SUCCESS [{idx}/{len(md_file_paths)}]: {doc_name} ({len(content):,} chars)")
            
        except Exception as e:
            print(f"❌ ERROR [{idx}/{len(md_file_paths)}]: Failed to read {md_path.name}: {e}")
            documents_failed += 1
    
    # Placeholder for feasibility report
    unified_content.append("\n## FEASIBILITY REPORT\n")
    unified_content.append("*(To be generated)*\n")
    
    # Write unified context file
    final_content = "\n".join(unified_content)
    total_chars = len(final_content)
    
    try:
        with open(unified_file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"\n{'='*60}")
        print(f"✅ Unified context file created successfully!")
        print(f"{'='*60}")
        print(f"📁 File path: {unified_file_path}")
        print(f"📊 Total size: {total_chars:,} characters")
        print(f"✅ Documents processed: {documents_processed}")
        print(f"❌ Documents failed: {documents_failed}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to write unified context file: {e}")
        raise
    
    return {
        "file_path": str(unified_file_path.absolute()),
        "total_chars": total_chars,
        "documents_processed": documents_processed,
        "documents_failed": documents_failed
    }


def _update_unified_context_with_report(unified_path: str, feasibility_report: str) -> bool:
    """
    Update the unified context file with the generated feasibility report.
    
    Args:
        unified_path: Path to the unified context file
        feasibility_report: Generated feasibility report content
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Updating unified context file with feasibility report")
    print(f"{'='*60}\n")
    
    try:
        # Read current content
        with open(unified_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify placeholder exists
        placeholder = "## FEASIBILITY REPORT\n\n*(To be generated)*"
        if placeholder not in content:
            print(f"⚠️  WARNING: Placeholder not found in unified context file")
            print(f"   File may have been modified or report already added")
            return False
        
        # Replace placeholder with actual report
        updated_content = content.replace(
            placeholder,
            f"## FEASIBILITY REPORT\n\n{feasibility_report}"
        )
        
        # Write updated content
        with open(unified_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Unified context file updated successfully!")
        print(f"📊 Report size: {len(feasibility_report):,} characters")
        print(f"📊 Total file size: {len(updated_content):,} characters")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to update unified context file: {e}")
        return False


def _validate_generation_result(result: dict, stage: str) -> Dict[str, Any]:
    """
    Validate the result from feasibility agent.
    
    Args:
        result: Result dictionary from generate_feasibility_questions
        stage: "thinking_summary" or "feasibility_report"
        
    Returns:
        dict: Validation report
    """
    validation = {
        "is_valid": False,
        "has_content": False,
        "content_length": 0,
        "warnings": []
    }
    
    content = result.get(stage, "")
    
    if not content:
        validation["warnings"].append(f"{stage} is empty")
        return validation
    
    validation["has_content"] = True
    validation["content_length"] = len(content)
    
    # Check for error messages
    if "Error" in content or "error" in content[:100]:
        validation["warnings"].append(f"{stage} may contain error message")
    
    # Check minimum length (thinking summary should be substantial)
    min_length = 100 if stage == "thinking_summary" else 500
    if len(content) < min_length:
        validation["warnings"].append(f"{stage} is suspiciously short ({len(content)} chars < {min_length})")
    
    # Check for delimiter issues (thinking summary)
    if stage == "thinking_summary":
        if "---THINKING_SUMMARY_START---" not in content:
            validation["warnings"].append("Thinking summary delimiters not found - fallback was used")
    
    # If no warnings, mark as valid
    validation["is_valid"] = len(validation["warnings"]) == 0
    
    return validation


def _generate_assessment(state: FeasibilityState) -> dict:
    """Generate feasibility assessment (thinking + report)."""
    from src.app.feasibility_agent import generate_feasibility_questions
    
    print(f"\n{'#'*60}")
    print(f"# FEASIBILITY GRAPH: GENERATE ASSESSMENT NODE")
    print(f"{'#'*60}\n")
    
    # Create unified context file from MD files
    md_file_paths = state.md_file_paths or []
    session_id = state.session_id
    
    print(f"📋 Session ID: {session_id[:8]}...")
    print(f"📄 Processing {len(md_file_paths)} MD files\n")
    
    # Create unified context and get metadata
    context_result = _create_unified_context_file(md_file_paths, session_id)
    unified_context_path = context_result["file_path"]
    
    # Validate that documents were actually processed
    if context_result["documents_processed"] == 0:
        print(f"❌ CRITICAL: No documents were processed!")
        return {
            "thinking_summary": "ERROR: No documents were processed",
            "feasibility_report": "ERROR: No documents were processed",
            "unified_context_path": unified_context_path
        }
    
    print(f"🤖 Invoking feasibility agent...\n")
    
    # Generate feasibility questions
    result = generate_feasibility_questions(
        context_file_path=unified_context_path,
        development_context=state.development_context,
        session_id=session_id
    )
    
    # Validate thinking summary
    print(f"\n{'='*60}")
    print(f"Validating Stage 1: Thinking Summary")
    print(f"{'='*60}")
    thinking_validation = _validate_generation_result(result, "thinking_summary")
    print(f"Valid: {thinking_validation['is_valid']}")
    print(f"Has content: {thinking_validation['has_content']}")
    print(f"Content length: {thinking_validation['content_length']:,} chars")
    if thinking_validation['warnings']:
        for warning in thinking_validation['warnings']:
            print(f"⚠️  {warning}")
    print()
    
    # Validate feasibility report
    print(f"{'='*60}")
    print(f"Validating Stage 2: Feasibility Report")
    print(f"{'='*60}")
    report_validation = _validate_generation_result(result, "feasibility_report")
    print(f"Valid: {report_validation['is_valid']}")
    print(f"Has content: {report_validation['has_content']}")
    print(f"Content length: {report_validation['content_length']:,} chars")
    if report_validation['warnings']:
        for warning in report_validation['warnings']:
            print(f"⚠️  {warning}")
    print()
    
    # Update unified context file with feasibility report
    if report_validation['has_content']:
        update_success = _update_unified_context_with_report(
            unified_context_path,
            result.get("feasibility_report", "")
        )
        if not update_success:
            print(f"⚠️  WARNING: Failed to update unified context file with report")
    
    print(f"\n{'#'*60}")
    print(f"# FEASIBILITY ASSESSMENT GENERATION COMPLETE")
    print(f"{'#'*60}\n")
    
    return {
        "thinking_summary": result.get("thinking_summary", ""),
        "feasibility_report": result.get("feasibility_report", ""),
        "unified_context_path": unified_context_path
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
