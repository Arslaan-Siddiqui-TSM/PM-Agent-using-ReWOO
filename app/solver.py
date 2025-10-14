from states.rewoo_state import ReWOO
from config.llm_config import model
import os
import time


def solve(state: ReWOO):
    """Solve the given ReWOO state by generating a project plan.

    Args:
        state (ReWOO): The ReWOO state containing the task and plan information.

    Returns:
        dict: The result of the solving process, including the generated project plan.
    """

    plan = ""
    if state.steps is None:
        return {"result": "No steps available to solve the task."}
    for _plan, step_name, tool, tool_input in state.steps:
        _results = (state.results or {}) if hasattr(state, "results") else {}
        for k, v in _results.items():
            tool_input = tool_input.replace(k, v)
            step_name = step_name.replace(k, v)
        plan += f"Plan: {_plan}\n{step_name} = {tool}[{tool_input}]"
    
    prompt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts", "solver_prompt.txt"))
    with open(prompt_path, "r", encoding="utf-8") as f:
        solve_prompt = f.read()
    prompt = solve_prompt.format(plan=plan, task=state.task)
    result = model.invoke(prompt)
    
    # Save the Markdown result to a file
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"project_plan_{time.strftime('%Y%m%d_%H%M%S')}.md")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(result.content))

    print(f"\n✅ Project plan saved to: {file_path}\n")

    return {"result": result.content}
