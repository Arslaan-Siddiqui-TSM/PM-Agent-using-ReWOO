from __future__ import annotations

import os
from typing import Dict

from config.llm_config import model
from states.reflection_state import ReflectionState
from utils.helper import get_global_logger, load_feasibility_answers, load_prompt_template


def generate_reflection(state: ReflectionState) -> Dict[str, object]:
    """Critique the current draft and capture feedback for revisions."""

    if not state.iterations or not state.current_draft:
        raise ValueError("Cannot reflect without an existing draft.")

    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "prompts", "reflect_prompt.txt")
    )
    prompt_template = load_prompt_template(prompt_path)

    feasibility_context = (
        load_feasibility_answers(state.feasibility_file_path)
        if state.feasibility_file_path
        else None
    ) or "No feasibility notes supplied. Flag missing governance details."

    formatted_prompt = prompt_template.format(
        task=state.task or "Create a comprehensive software project plan.",
        feasibility_context=feasibility_context,
        document_context=state.document_context or "Document context unavailable.",
        current_draft=state.current_draft,
    )

    result = model.invoke(formatted_prompt)
    critique_text = str(getattr(result, "content", result)).strip()

    iterations = list(state.iterations)
    latest_iteration = iterations[-1].model_copy()
    latest_iteration.critique = critique_text
    iterations[-1] = latest_iteration

    logger = get_global_logger()
    if logger:
        logger.log_llm_interaction(
            stage="Reflection Agent - Critique",
            prompt=formatted_prompt,
            response=critique_text,
            additional_context={
                "Iteration": len(iterations),
            },
        )

    return {
        "iterations": iterations,
        "current_critique": critique_text,
    }
