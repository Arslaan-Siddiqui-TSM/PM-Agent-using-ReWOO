import os
import re
from states.rewoo_state import ReWOO
from langchain_core.prompts import ChatPromptTemplate
from config.llm_config import model


def get_plan(state: ReWOO) -> dict:
    """Generate a project plan based on the provided prompt and task.

    Args:
        state (ReWOO): The current state of the ReWOO process containing the task.

    Returns:
        dict: A dictionary containing the generated plan steps and other relevant information.
    """
    # Read the prompt from the file directly to avoid circular imports
    prompt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts", "planner_prompt.txt"))
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()
    task = state.task

    result = model.invoke(prompt.format(task=task))

    # Regex to match expressions of the form E#... = ...[...]
    regex_pattern = r"Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]"
    prompt_template = ChatPromptTemplate.from_messages([("human", prompt)])
    planner = prompt_template | model

    current_task = state.task
    result = planner.invoke({"task": current_task})
    # Find all matches in the sample text
    if result.content is None:
        matches = []
    else:
        matches = re.findall(regex_pattern, str(result.content))
    return {"steps": matches, "plan_string": str(result.content)}