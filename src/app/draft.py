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


def generate_draft(state: ReflectionState) -> Dict[str, object]:
    """Generate the next project plan draft using contextual inputs."""

    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "prompts", "draft_prompt.txt")
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
        files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "files"))
        document_context = load_all_documents_from_directory(files_dir)
        context_source = "Raw PDF ingestion"

    revision_guidance = state.revision_instructions or "None. Produce the strongest possible initial plan."

    formatted_prompt = prompt_template.format(
        task=(state.task or DEFAULT_TASK_PLACEHOLDER),
        feasibility_context=feasibility_context,
        document_context=document_context,
        revision_guidance=revision_guidance,
    )

    result = model.invoke(formatted_prompt)
    draft_text = str(getattr(result, "content", result)).strip()

    iteration_reasoning = (
        f"Revision focus: {revision_guidance}" if state.revision_instructions else "Initial draft"
    )

    iterations = list(state.iterations)
    iterations.append(
        ReflectionIteration(
            draft=draft_text,
            reasoning=iteration_reasoning,
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
                "Revision Guidance Used": "Yes" if state.revision_instructions else "No",
                "Total Iterations": len(iterations),
            },
        )

    return {
        "iterations": iterations,
        "current_draft": draft_text,
        "current_critique": None,
        "revision_instructions": None,
        "decision_rationale": None,
        "context_source": context_source,
        "revision_focus": revision_guidance if state.revision_instructions else None,
    }
