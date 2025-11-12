from __future__ import annotations

import os
from typing import Dict

from src.config.llm_config import model
from src.states.reflection_state import ReflectionIteration, ReflectionState
from src.utils.helper import (
    get_global_logger,
    load_all_documents_from_directory,
    load_feasibility_answers,
    load_prompt_template,
)


DEFAULT_TASK_PLACEHOLDER = "Create a comprehensive software project plan."


def _build_iteration_context(state: ReflectionState, iteration_number: int) -> str:
    """Build comprehensive iteration context from state for prompt injection."""
    
    if iteration_number == 0:
        return "This is the initial draft (Iteration 1). No prior iterations exist."
    
    # Build iteration progress summary
    context_lines = [
        f"## ITERATION PROGRESS:",
        f"- Current iteration: {iteration_number + 1} of {state.max_iterations}",
    ]
    
    # Add quality score progression if available
    if state.quality_scores:
        scores_str = ", ".join([f"Iteration {i+1}: {score:.1f}/10" for i, score in enumerate(state.quality_scores)])
        context_lines.append(f"- Quality progression: {scores_str}")
    
    # Add past critiques summary
    if state.iterations:
        context_lines.append("\n## PAST CRITIQUES:")
        for i, iteration in enumerate(state.iterations):
            if iteration.critique:
                # Truncate long critiques for context efficiency
                critique_summary = iteration.critique[:200] + "..." if len(iteration.critique) > 200 else iteration.critique
                context_lines.append(f"**Iteration {i+1}**: {critique_summary}")
    
    # Add improvement areas identified
    if state.improvement_areas:
        context_lines.append("\n## FOCUS AREAS FOR THIS ITERATION:")
        for area in state.improvement_areas[-3:]:  # Last 3 focus areas
            context_lines.append(f"- {area}")
    
    # Add addressed issues to avoid regression
    if state.addressed_issues:
        context_lines.append("\n## PREVIOUSLY ADDRESSED (Do not regress):")
        for issue in state.addressed_issues[-5:]:  # Last 5 addressed issues
            context_lines.append(f"✓ {issue}")
    
    # Add iteration summaries
    if state.iteration_summaries:
        context_lines.append("\n## ITERATION HISTORY:")
        for i, summary in enumerate(state.iteration_summaries):
            context_lines.append(f"**Iteration {i+1}**: {summary}")
    
    return "\n".join(context_lines)


def generate_draft(state: ReflectionState) -> Dict[str, object]:
    """Generate the next project plan draft using contextual inputs."""

    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "project_plan_draft.txt")
    )
    prompt_template = load_prompt_template(prompt_path)

    feasibility_context = (
        load_feasibility_answers(state.feasibility_file_path)
        if state.feasibility_file_path
        else None
    ) or "No feasibility notes were provided. Capture any assumptions explicitly."

    if state.document_context:
        document_context = state.document_context
        context_source = "Document Intelligence Pipeline"
    else:
        files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "files"))
        document_context = load_all_documents_from_directory(files_dir)
        context_source = "Raw PDF ingestion"

    # Note: revision_guidance comes from graph/routing logic, not stored in state
    revision_guidance = "None. Produce the strongest possible initial plan."
    
    # Build iteration context from state
    iteration_number = len(state.iterations)
    iteration_context = _build_iteration_context(state, iteration_number)

    formatted_prompt = prompt_template.format(
        pm_inputs=(state.task or DEFAULT_TASK_PLACEHOLDER),
        feasibility_report=feasibility_context,
        initial_documents=document_context,
        revision_guidance=revision_guidance,
        iteration_context=iteration_context,
    )

    result = model.invoke(formatted_prompt)
    draft_text = str(getattr(result, "content", result)).strip()

    iterations = list(state.iterations)
    iterations.append(
        ReflectionIteration(
            draft=draft_text,
        )
    )

    logger = get_global_logger()
    if logger:
        logger.log_llm_interaction(
            stage="Reflection Agent - Draft",
            prompt=formatted_prompt,
            response=draft_text,
            additional_context={
                "Context Source": context_source,
                "Total Iterations": len(iterations),
            },
        )

    return {
        "iterations": iterations,
    }
