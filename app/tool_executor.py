from states.rewoo_state import ReWOO
from utils.helper import get_current_task, truncate_query
from tools.search_tool import search
from config.llm_config import model
import fitz


def tool_execution(state: ReWOO):
    """Worker node that executes the tools of a given plan."""
    _step = get_current_task(state)
    if state.steps is None or _step is None or _step - 1 >= len(state.steps):
        raise ValueError("No steps available to execute.")
    _, step_name, tool, tool_input = state.steps[_step - 1]
    _results = (state.results or {}) if hasattr(state, "results") else {}
    for k, v in _results.items():
        tool_input = tool_input.replace(k, v)

    if tool == "Google":
        # Validate and truncate query length
        original_query = tool_input
        if len(original_query) > 400:
            truncated_query = truncate_query(original_query, 400)
            print(f"Warning: Query too long ({len(original_query)} chars). Truncated to {len(truncated_query)} chars.")
            print(f"Original: {original_query}")
            print(f"Truncated: {truncated_query}")
            tool_input = truncated_query

        result = search.invoke(tool_input)
    
    elif tool == "LLM":
        result = model.invoke(tool_input)
    
    elif tool == "FileReader":
        file_path = tool_input.strip().strip("'").strip('"')
        try:
            with fitz.open(file_path) as doc:
                text = ""
                for page in doc:
                    page_text = page.get_text("text")
                    text += str(page_text)
            result = text.strip()
        except Exception as e:
            result = f"Error reading file: {str(e)}"
    else:
        raise ValueError(f"Unknown tool: {tool}")

    _results[step_name] = str(result)
    return {"results": _results}