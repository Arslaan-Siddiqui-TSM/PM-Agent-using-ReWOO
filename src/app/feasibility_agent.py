import os
import json
from pathlib import Path
from src.config.llm_config import model
from rich.console import Console
from rich.panel import Panel


console = Console()


# ============================================================================
# Helper Functions for Two-Stage Feasibility Generation
# ============================================================================

def _extract_thinking_summary(content_str: str) -> str:
    """
    Extract thinking summary from Stage 1 LLM response.
    
    Handles:
    - Delimited format with ---THINKING_SUMMARY_START--- and ---THINKING_SUMMARY_END---
    - Code fences around delimited content
    - Fallback to entire content if delimiters not found
    """
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Extracting thinking summary from Stage 1 response")
    
    # Optional: strip surrounding code fences if present
    cs_strip = content_str.strip()
    if cs_strip.startswith("```") and cs_strip.endswith("```"):
        console.print("[bold yellow]DEBUG:[/bold yellow] Stripping surrounding code fences from response")
        cs_body = cs_strip[3:]
        nl = cs_body.find("\n")
        if nl != -1:
            cs_body = cs_body[nl+1:]
        cs_body = cs_body.rstrip("`")
        content_str = cs_body.strip()

    # Try robust regex-based extraction
    import re as _re
    think_pat = _re.compile(
        r"---THINKING_SUMMARY_START---\s*(.*?)\s*(?:---THINKING_SUMMARY_END---|\Z)",
        _re.DOTALL,
    )

    m_think = think_pat.search(content_str)
    if m_think:
        thinking_summary = m_think.group(1).strip()
        console.print(f"[bold green]DEBUG:[/bold green] Extracted thinking summary via regex (len={len(thinking_summary)})")
        return thinking_summary
    
    # Fallback: use entire content
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Delimiters not found, using entire response as thinking summary")
    return content_str.strip()


def _build_stage2_prompt(thinking_summary: str, user_payload: dict, session_id: str) -> str:
    """
    Build Stage 2 prompt for feasibility report generation.
    
    Combines:
    - Stage 2 template (feasibility_report.txt)
    - Thinking summary from Stage 1
    - Original development_context and documents
    """
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Building Stage 2 prompt")
    
    # Load Stage 2 template
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "feasibility_report.txt"
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Loading Stage 2 template from: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            stage2_template = f.read()
        console.print(f"[bold green]DEBUG:[/bold green] Stage 2 template loaded, length: {len(stage2_template)} characters")
    except Exception as e:
        console.print(f"[bold red]ERROR:[/bold red] Failed to load Stage 2 template: {e}")
        raise
    
    # Build user message for Stage 2
    stage2_payload = {
        "thinking_summary": thinking_summary,
        "development_context": user_payload.get("development_context", {}),
        "documents": user_payload.get("documents", user_payload.get("documents_summary", {})),
        "session_id": session_id
    }
    
    user_message_stage2 = json.dumps(stage2_payload, ensure_ascii=False, indent=2)
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Stage 2 user payload length: {len(user_message_stage2)} characters")
    
    # Combine template and payload
    full_prompt_stage2 = f"{stage2_template}\n\n---\n\nUSER PAYLOAD:\n\n{user_message_stage2}"
    
    console.print(f"[bold green]DEBUG:[/bold green] Stage 2 prompt built, total length: {len(full_prompt_stage2)} characters")
    
    return full_prompt_stage2


def generate_feasibility_questions(document_text: str, development_context: dict | None = None, session_id: str = "unknown", md_file_paths: list[str] | None = None) -> dict:
    """Generate feasibility questions for the Tech Lead review.

    Args:
        document_text (str): The markdown text content from parsed documents.
        development_context (dict, optional): Development process information from user.
        session_id (str, optional): Session ID for the assessment.

    Returns:
        dict: Dictionary with keys 'thinking_summary' and 'feasibility_report' containing markdown text.
    """    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Starting feasibility question generation")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Input document text length: {len(document_text)} characters")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Development context provided: {development_context is not None}")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Session ID: {session_id}")
    
    # Get project root directory (two levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    
    # Load Stage 1 prompt (Thinking Summary)
    prompt_path = project_root / "prompts" / "thinking_summary.txt"
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Loading Stage 1 prompt from: {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] System prompt loaded, length: {len(system_prompt)} characters")
    
    # Prepare text input from MD files
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Using MD file text input")
    
    # Truncate document text if too long (keep reasonable limit for token budget)
    max_doc_length = 150000  # Allows larger context for modern LLMs
    if len(document_text) > max_doc_length:
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Truncating document text to {max_doc_length} characters")
        document_text = document_text[:max_doc_length]
    
    # If development_context is None, provide an empty dict with "unknown" placeholder
    if development_context is None:
        development_context = {
            "note": "No development context provided by user",
            "teamSize": "unknown",
            "timeline": "unknown",
            "budget": "unknown",
            "methodology": "unknown",
            "techStack": "unknown",
            "constraints": "unknown"
        }
    
    # Build payload with MD text content
    user_payload = {
        "development_context": development_context,
        "documents_summary": {
            "session_id": session_id,
            "content": document_text,
            "source": "markdown files"
        }
    }
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Using MD text payload format")
    
    # Build the full prompt with system instructions + JSON payload
    user_message = json.dumps(user_payload, ensure_ascii=False, indent=2)
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] User payload length: {len(user_message)} characters")
    
    # Combine system prompt and user message
    full_prompt = f"{system_prompt}\n\n---\n\nUSER PAYLOAD:\n\n{user_message}"
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Full prompt length: {len(full_prompt)} characters")
    
    # Show a preview of the prompt
    console.print("\n[bold magenta]DEBUG - PROMPT PREVIEW:[/bold magenta]")
    console.print("[dim]" + "="*80 + "[/dim]")
    console.print(f"[cyan]Total prompt characters: {len(full_prompt)}[/cyan]")
    console.print(f"[cyan]User payload preview:[/cyan]")
    console.print(user_message[:500] + "..." if len(user_message) > 500 else user_message)
    console.print("[dim]" + "="*80 + "[/dim]\n")
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Starting two-stage feasibility generation...")
    
    try:
        # ============================================================
        # STAGE 1: Generate thinking summary
        # ============================================================
        console.print(f"\n[bold cyan]═══ STAGE 1: GENERATING THINKING SUMMARY ═══[/bold cyan]")
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Invoking LLM for Stage 1 (thinking summary)")
        
        result_stage1 = model.invoke(full_prompt)
        content_stage1 = str(getattr(result_stage1, "content", result_stage1))
        
        console.print(f"[bold green]DEBUG:[/bold green] Stage 1 LLM invocation successful")
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Stage 1 content length: {len(content_stage1)} characters")
        
        # Extract thinking summary from Stage 1
        thinking_summary = _extract_thinking_summary(content_stage1)
        console.print(f"[bold green]✓ STAGE 1 COMPLETE:[/bold green] Thinking summary: {len(thinking_summary)} chars")
        
        # ============================================================
        # STAGE 2: Generate feasibility report from thinking summary
        # ============================================================
        console.print(f"\n[bold cyan]═══ STAGE 2: GENERATING FEASIBILITY REPORT ═══[/bold cyan]")
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Building Stage 2 prompt with thinking summary")
        
        stage2_prompt = _build_stage2_prompt(thinking_summary, user_payload, session_id)
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Stage 2 prompt length: {len(stage2_prompt)} characters")
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Invoking LLM for Stage 2 (feasibility report)")
        
        result_stage2 = model.invoke(stage2_prompt)
        content_stage2 = str(getattr(result_stage2, "content", result_stage2))
        
        console.print(f"[bold green]DEBUG:[/bold green] Stage 2 LLM invocation successful")
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Stage 2 content length: {len(content_stage2)} characters")
        
        # Extract feasibility report from Stage 2 (entire response is the report)
        feasibility_report = content_stage2.strip()
        console.print(f"[bold green]✓ STAGE 2 COMPLETE:[/bold green] Feasibility report: {len(feasibility_report)} chars")
        
        console.print(f"\n[bold green]═══ TWO-STAGE GENERATION COMPLETED SUCCESSFULLY ═══[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]DEBUG ERROR:[/bold red] LLM invocation failed: {e}")
        return {
            "thinking_summary": f"Error calling LLM: {e}",
            "feasibility_report": f"Error calling LLM: {e}"
        }

    return {
        "thinking_summary": thinking_summary,
        "feasibility_report": feasibility_report
    }


def save_development_context_to_json(
    development_context: dict,
    session_id: str,
    output_dir: str = "outputs/intermediate"
) -> str:
    """Save development context data to a JSON file.
    
    Args:
        development_context (dict): Dictionary containing form data from frontend
            (methodology, teamSize, timeline, budget, techStack, constraints).
        session_id (str): Session ID associated with this context.
        output_dir (str, optional): Directory to save the JSON file. 
            Defaults to "outputs/intermediate".
    
    Returns:
        str: The path to the saved JSON file.
    """
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Saving development context to JSON")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Session ID: {session_id}")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Output directory: {output_dir}")
    
    import json
    from datetime import datetime
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename with session ID and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"development_context_{session_id[:8]}_{timestamp}.json"
    json_file_path = os.path.join(output_dir, json_filename)
    
    # Prepare the JSON data structure
    json_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "development_context": development_context,
    }
    
    # Save to JSON file
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"[bold green]DEBUG:[/bold green] Development context saved to: {json_file_path}")
    return json_file_path


if __name__ == "__main__":
    console.print(f"[bold yellow]This module is not meant to be run directly.[/bold yellow]")
    console.print(f"[bold cyan]Use the API endpoints for feasibility generation.[/bold cyan]")