from __future__ import annotations

import json
import os
from typing import Dict

from config.llm_config import model
from states.reflection_state import ReflectionIteration, ReflectionState
from utils.helper import get_global_logger, load_feasibility_answers, load_prompt_template


def _safe_parse_json(payload: str) -> Dict[str, str]:
    """Best-effort JSON parsing with fallback for stray text."""

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = payload[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                pass
        raise


def apply_revision(state: ReflectionState) -> Dict[str, object]:
    """Decide whether to accept the draft or request revisions."""

    if not state.iterations or not state.current_draft:
        raise ValueError("Cannot revise without an existing draft.")

    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "prompts", "revise_prompt.txt")
    )
    prompt_template = load_prompt_template(prompt_path)

    feasibility_context = (
        load_feasibility_answers(state.feasibility_file_path)
        if state.feasibility_file_path
        else None
    ) or "Feasibility notes unavailable."

    formatted_prompt = prompt_template.format(
        task=state.task or "Create a comprehensive software project plan.",
        feasibility_context=feasibility_context,
        document_context=state.document_context or "Document context unavailable.",
        current_draft=state.current_draft,
        critique=state.current_critique or "No critique generated.",
    )

    result = model.invoke(formatted_prompt)
    raw_response = str(getattr(result, "content", result)).strip()

    decision_payload = _safe_parse_json(raw_response)

    decision = str(decision_payload.get("decision", "")).strip().lower()
    rationale = str(decision_payload.get("rationale", "")).strip()
    required_actions = str(decision_payload.get("required_actions", "")).strip()

    iterations = list(state.iterations)
    latest_iteration = iterations[-1].model_copy()
    latest_iteration.accepted = decision == "accept"
    if rationale:
        latest_iteration.reasoning = (
            f"{latest_iteration.reasoning or ''}\nDecision rationale: {rationale}"
        ).strip()
    iterations[-1] = latest_iteration

    logger = get_global_logger()
    if logger:
        logger.log_llm_interaction(
            stage="Reflection Agent - Revise",
            prompt=formatted_prompt,
            response=raw_response,
            additional_context={
                "Decision": decision,
                "Has Required Actions": "yes" if required_actions else "no",
                "Iteration": len(iterations),
            },
        )

    if decision == "accept":
        # Finalize with the approved plan.
        return {
            "iterations": iterations,
            "decision_rationale": rationale,
            "final_plan": state.current_draft,
            "revision_instructions": None,
            "decision": "accept",
            "required_actions": "",
        }

    if len(iterations) >= state.max_iterations:
        # Hit iteration cap; accept best effort to avoid infinite loop.
        iterations[-1].accepted = True
        return {
            "iterations": iterations,
            "decision_rationale": "Iteration cap reached. Returning best available draft.",
            "final_plan": state.current_draft,
            "revision_instructions": None,
            "decision": "forced-accept",
            "required_actions": required_actions,
        }

    # Request another cycle: instruct the draft node what to fix.
    return {
        "iterations": iterations,
        "current_critique": None,
        "decision_rationale": rationale,
        "revision_instructions": required_actions or None,
        "decision": "revise",
        "required_actions": required_actions,
    }
