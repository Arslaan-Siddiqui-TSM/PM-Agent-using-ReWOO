from __future__ import annotations

import json
import os
from typing import Dict

from src.config.llm_config import model
from src.states.reflection_state import ReflectionIteration, ReflectionState
from src.utils.helper import get_global_logger, load_feasibility_answers, load_prompt_template


def _build_revision_context(state: ReflectionState, iteration_number: int) -> str:
    """Build comprehensive iteration context for revision decision prompt."""
    
    if iteration_number == 0:
        return "This is the initial draft. No prior revision history exists."
    
    context_lines = [
        f"## REVISION DECISION CONTEXT:",
        f"- Current iteration: {iteration_number} of {state.max_iterations}",
    ]
    
    # Quality progression
    if state.quality_scores:
        scores_str = ", ".join([f"v{i+1}: {score:.1f}" for i, score in enumerate(state.quality_scores)])
        context_lines.append(f"- Quality trend: {scores_str}")
        
        # Calculate improvement
        if len(state.quality_scores) >= 2:
            improvement = state.quality_scores[-1] - state.quality_scores[-2]
            if improvement > 0:
                context_lines.append(f"- Last iteration improved by: +{improvement:.1f} points")
            elif improvement < 0:
                context_lines.append(f"- Last iteration regressed by: {improvement:.1f} points")
            else:
                context_lines.append(f"- Quality plateaued (no improvement)")
    
    # Past decisions
    if state.iterations:
        accepted_count = sum(1 for it in state.iterations if it.accepted)
        rejected_count = len(state.iterations) - accepted_count
        context_lines.append(f"- Past decisions: {accepted_count} accepted, {rejected_count} revised")
    
    # Iteration summaries
    if state.iteration_summaries:
        context_lines.append("\n## ITERATION HISTORY:")
        for summary in state.iteration_summaries:
            context_lines.append(f"- {summary}")
    
    # Outstanding focus areas
    if state.improvement_areas:
        recent_areas = state.improvement_areas[-3:]  # Last 3
        context_lines.append("\n## CURRENT FOCUS AREAS:")
        for area in recent_areas:
            context_lines.append(f"- {area}")
    
    # Addressed issues
    if state.addressed_issues:
        context_lines.append("\n## PREVIOUSLY RESOLVED:")
        for issue in state.addressed_issues[-5:]:
            context_lines.append(f"✓ {issue}")
    
    return "\n".join(context_lines)


def _safe_parse_json(payload: str) -> Dict[str, str]:
    """Bulletproof JSON parsing with extensive fallback handling."""
    
    original_payload = payload  # Keep for debugging
    
    # Step 1: Strip all whitespace
    payload = payload.strip()
    
    # Step 2: Remove ALL markdown code fences (handle multiple formats)
    # Handle ```json, ```, or any variant
    while payload.startswith("```"):
        # Find first newline after opening fence
        first_newline = payload.find("\n")
        if first_newline != -1:
            payload = payload[first_newline + 1:].strip()
        else:
            # No newline? Just remove the backticks
            payload = payload[3:].strip()
    
    # Remove closing fences
    while payload.endswith("```"):
        payload = payload[:-3].strip()
    
    # Step 3: Find the actual JSON object between { and }
    # This is foolproof - we extract ONLY what's between braces
    json_start = payload.find("{")
    json_end = payload.rfind("}")
    
    if json_start == -1 or json_end == -1 or json_end <= json_start:
        # No valid JSON braces found
        print(f"\n{'='*80}", flush=True)
        print(f"FATAL: NO JSON BRACES FOUND", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Original payload length: {len(original_payload)}", flush=True)
        print(f"Payload after processing:\n{payload[:1000]}", flush=True)
        print(f"{'='*80}\n", flush=True)
        raise ValueError(f"No JSON object (missing braces) in LLM response")
    
    # Extract ONLY what's between the braces (inclusive)
    json_str = payload[json_start : json_end + 1].strip()
    
    # Step 4: Try to parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Still failed - show detailed debug info
        print(f"\n{'='*80}", flush=True)
        print(f"JSON PARSE ERROR AFTER EXTRACTION", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Original payload (first 500 chars):\n{original_payload[:500]}\n", flush=True)
        print(f"Extracted JSON (first 500 chars):\n{json_str[:500]}", flush=True)
        print(f"Extracted JSON (last 200 chars):\n{json_str[-200:]}", flush=True)
        print(f"Error: {str(e)}", flush=True)
        print(f"Error position: {e.pos if hasattr(e, 'pos') else 'N/A'}", flush=True)
        print(f"{'='*80}\n", flush=True)
        raise ValueError(f"JSON parse failed: {str(e)}")


def apply_revision(state: ReflectionState) -> Dict[str, object]:
    """Decide whether to accept the draft or request revisions."""
    
    print("\n" + "="*80, flush=True)
    print("🔥 REVISE NODE STARTED - USING NEW CODE 🔥", flush=True)
    print("="*80 + "\n", flush=True)

    if not state.iterations or not state.current_draft:
        raise ValueError("Cannot revise without an existing draft.")
    
    print("✓ State validation passed", flush=True)

    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "project_plan_revise.txt")
    )
    print(f"✓ Prompt path: {prompt_path}", flush=True)
    
    prompt_template = load_prompt_template(prompt_path)
    print(f"✓ Prompt template loaded ({len(prompt_template)} chars)", flush=True)

    print("→ Loading feasibility context...", flush=True)
    feasibility_context = (
        load_feasibility_answers(state.feasibility_file_path)
        if state.feasibility_file_path
        else None
    ) or "Feasibility notes unavailable."
    print(f"✓ Feasibility context loaded ({len(feasibility_context)} chars)", flush=True)
    
    # Build iteration context for revision decision
    iteration_number = len(state.iterations)
    iteration_context = _build_revision_context(state, iteration_number)

    print("→ Formatting prompt...", flush=True)
    
    try:
        # Escape curly braces in variables to prevent format() errors
        print("  → Escaping curly braces in variables...", flush=True)
        pm_inputs_safe = (state.task or "Create a comprehensive software project plan.").replace("{", "{{").replace("}", "}}")
        feasibility_safe = feasibility_context.replace("{", "{{").replace("}", "}}")
        documents_safe = (state.document_context or "Document context unavailable.").replace("{", "{{").replace("}", "}}")
        draft_safe = state.current_draft.replace("{", "{{").replace("}", "}}")
        critique_safe = (state.current_critique or "No critique generated.").replace("{", "{{").replace("}", "}}")
        iteration_context_safe = iteration_context.replace("{", "{{").replace("}", "}}")
        print("  ✓ Variables escaped", flush=True)
        
        print("  → Calling prompt_template.format()...", flush=True)
        formatted_prompt = prompt_template.format(
            pm_inputs=pm_inputs_safe,
            feasibility_report=feasibility_safe,
            initial_documents=documents_safe,
            draft_project_plan=draft_safe,
            reflection_critique=critique_safe,
            iteration_context=iteration_context_safe,
        )
        print(f"✓ Prompt formatted ({len(formatted_prompt)} chars)", flush=True)
        
    except KeyError as ke:
        print(f"\n{'='*80}", flush=True)
        print(f"❌ ERROR IN PROMPT FORMATTING (KeyError)", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Missing key: {ke}", flush=True)
        print(f"This means the prompt template references a variable that wasn't provided", flush=True)
        print(f"{'='*80}\n", flush=True)
        raise
    except Exception as fmt_error:
        print(f"\n{'='*80}", flush=True)
        print(f"❌ ERROR IN PROMPT FORMATTING", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Error type: {type(fmt_error).__name__}", flush=True)
        print(f"Error message: {str(fmt_error)}", flush=True)
        print(f"{'='*80}\n", flush=True)
        import traceback
        traceback.print_exc()
        raise
    
    print("📞 About to invoke LLM for revision decision...", flush=True)
    
    # Add comprehensive error handling around LLM call
    try:
        result = model.invoke(formatted_prompt)
        print("✅ LLM invocation successful!", flush=True)
        
        # Extract response with detailed logging
        raw_response = str(getattr(result, "content", result)).strip()
        print(f"✅ Response extracted: {len(raw_response)} chars", flush=True)
        
    except Exception as llm_error:
        print(f"\n{'='*80}", flush=True)
        print(f"❌ ERROR DURING LLM INVOCATION", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Error type: {type(llm_error).__name__}", flush=True)
        print(f"Error message: {str(llm_error)}", flush=True)
        print(f"{'='*80}\n", flush=True)
        import traceback
        traceback.print_exc()
        raise
    
    # Debug logging
    print(f"\n{'='*80}", flush=True)
    print(f"REVISE NODE - RAW LLM RESPONSE", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"Response length: {len(raw_response)} chars", flush=True)
    print(f"First 500 chars:\n{raw_response[:500]}", flush=True)
    if len(raw_response) > 500:
        print(f"\n[...truncated...]\n", flush=True)
        print(f"Last 200 chars:\n{raw_response[-200:]}", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    print("→ Parsing JSON decision...", flush=True)
    try:
        decision_payload = _safe_parse_json(raw_response)
        print(f"✅ JSON parsed successfully: {decision_payload.get('decision', 'N/A')}", flush=True)
    except Exception as parse_error:
        print(f"\n{'='*80}", flush=True)
        print(f"❌ ERROR DURING JSON PARSING", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Error type: {type(parse_error).__name__}", flush=True)
        print(f"Error message: {str(parse_error)}", flush=True)
        print(f"{'='*80}\n", flush=True)
        raise

    decision = str(decision_payload.get("decision", "")).strip().lower()
    rationale = str(decision_payload.get("rationale", "")).strip()
    required_actions = str(decision_payload.get("required_actions", "")).strip()

    iterations = list(state.iterations)
    latest_iteration = iterations[-1].model_copy()
    latest_iteration.accepted = decision == "accept"
    iterations[-1] = latest_iteration

    logger = get_global_logger()
    if logger:
        logger.log_llm_interaction(
            stage="Reflection Agent - Revise",
            prompt=formatted_prompt,
            response=raw_response,
            additional_context={
                "Decision": decision,
                "Rationale": rationale,
                "Has Required Actions": "yes" if required_actions else "no",
                "Iteration": len(iterations),
            },
        )

    if decision == "accept":
        # Finalize with the approved plan.
        # Mark current improvement areas as addressed
        addressed_issues = list(state.addressed_issues)
        if state.improvement_areas:
            addressed_issues.extend(state.improvement_areas[-3:])  # Last 3 focus areas now resolved
        
        return {
            "iterations": iterations,
            "final_plan": state.current_draft,
            "decision": "accept",
            "addressed_issues": addressed_issues,
        }

    if len(iterations) >= state.max_iterations:
        # Hit iteration cap; accept best effort to avoid infinite loop.
        iterations[-1].accepted = True
        
        # Mark as addressed even if forced
        addressed_issues = list(state.addressed_issues)
        if state.improvement_areas:
            addressed_issues.extend(state.improvement_areas[-3:])
        
        return {
            "iterations": iterations,
            "final_plan": state.current_draft,
            "decision": "forced-accept",
            "addressed_issues": addressed_issues,
        }

    # Request another cycle: instruct the draft node what to fix.
    return {
        "iterations": iterations,
        "decision": "revise",
    }
