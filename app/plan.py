import os, re
from states.rewoo_state import ReWOO
from config.llm_config import model
from utils.helper import load_feasibility_answers, load_all_documents_from_directory, get_global_logger


def get_plan(state: ReWOO) -> dict:
    """Generate a project plan based on the provided prompt and task.

    Args:
        state (ReWOO): The current state of the ReWOO process containing the task.

    Returns:
        dict: A dictionary containing the generated plan steps and other relevant information.
    """

    # Load the base prompt template
    prompt_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "prompts", "planner_prompt.txt")
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Load task and feasibility notes
    feasibility_context = load_feasibility_answers("outputs/feasibility_questions.md") or "No feasibility answers available yet."
    
    # Use intelligent document context if available, otherwise use legacy loading
    if state.document_context:
        documents_context = state.document_context
        context_source = "Document Intelligence Pipeline"
    else:
        # Legacy mode: Load all documents from the files directory
        files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "files"))
        documents_context = load_all_documents_from_directory(files_dir)
        context_source = "Legacy Document Loading"

    # Fill the placeholders
    formatted_prompt = prompt_template.format(
        feasibility_context=feasibility_context,
        documents_context=documents_context
    )

    # Call LLM to generate the planning steps
    result = model.invoke(formatted_prompt)

    # Log the complete LLM interaction
    logger = get_global_logger()
    if logger:
        logger.log_llm_interaction(
            stage="Planning",
            prompt=formatted_prompt,
            response=result.content,
            additional_context={
                "Context Source": context_source,
                "Feasibility Context Length": f"{len(feasibility_context)} characters",
                "Documents Context Length": f"{len(documents_context)} characters"
            }
        )

    # Extract the plan structure
    regex_pattern = r"Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]"
    matches = re.findall(regex_pattern, str(result.content or ""))

    return {"steps": matches, "plan_string": str(result.content or "")}