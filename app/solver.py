from states.rewoo_state import ReWOO
from config.llm_config import model
import os
import time
from utils.helper import load_feasibility_answers, get_global_logger


def solve(state: ReWOO):
    """Solve the given ReWOO state by generating a complete project plan in Markdown.

    Args:
        state (ReWOO): The ReWOO state containing the task, steps, and intermediate results.

    Returns:
        dict: The result of the solving process, including the generated project plan.
    """

    # Build the structured plan string from all steps
    plan = ""
    if state.steps is None:
        return {"result": "No steps available to solve the task."}

    for _plan, step_name, tool, tool_input in state.steps:
        _results = (state.results or {}) if hasattr(state, "results") else {}
        for k, v in _results.items():
            tool_input = tool_input.replace(k, v)
            step_name = step_name.replace(k, v)
        plan += f"Plan: {_plan}\n{step_name} = {tool}[{tool_input}]\n"

    # Load the solver prompt template
    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "prompts", "solver_prompt.txt")
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        solve_prompt = f.read()

    # Load feasibility context (if available)
    feasibility_context = load_feasibility_answers("outputs/feasibility_questions.md") or "No feasibility notes available yet."

    # Fill the prompt with dynamic data
    formatted_prompt = solve_prompt.format(
        plan=plan,
        feasibility_context=feasibility_context
    )

    # Generate the final project plan via LLM
    result = model.invoke(formatted_prompt)

    # Log the complete solver LLM interaction
    logger = get_global_logger()
    if logger:
        logger.log_llm_interaction(
            stage="Solver - Final Solution Generation",
            prompt=formatted_prompt,
            response=str(result.content),
            additional_context={
                "Number of Steps": len(state.steps) if state.steps else 0,
                "Plan Length": f"{len(plan)} characters",
                "Feasibility Context Length": f"{len(feasibility_context)} characters"
            }
        )

    # Save the result to a Markdown file with timestamp
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    os.makedirs(output_dir, exist_ok=True)

    file_name = f"project_plan_{time.strftime('%Y%m%d_%H%M%S')}.md"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(result.content))

    print(f"\n✅ Project plan successfully saved to: {file_path}\n")

    return {"result": result.content}