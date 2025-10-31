raise RuntimeError(
    "app.tool_executor has been removed. The reflection pattern no longer uses "
    "step-based tool execution. Tools are now invoked directly within draft/reflect/revise nodes."
)
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

    logger = get_global_logger()

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
        
        # Log Google search
        if logger:
            logger.log_llm_interaction(
                stage=f"Tool Execution - Google Search",
                prompt=f"Search Query: {tool_input}",
                response=str(result),
                additional_context={
                    "Evidence ID": step_name,
                    "Tool": "Google",
                    "Query Length": f"{len(tool_input)} characters"
                }
            )
    
    elif tool == "LLM":
        result = model.invoke(tool_input)
        
        # Log LLM interaction
        if logger:
            logger.log_llm_interaction(
                stage=f"Tool Execution - LLM",
                prompt=tool_input,
                response=str(result.content),
                additional_context={
                    "Evidence ID": step_name,
                    "Tool": "LLM",
                    "Step": f"{_step}"
                }
            )
    
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
        
        # Log FileReader interaction
        if logger:
            result_preview = result[:1000] + "... [truncated]" if len(result) > 1000 else result
            logger.log_llm_interaction(
                stage=f"Tool Execution - FileReader",
                prompt=f"File Path: {file_path}",
                response=result_preview,
                additional_context={
                    "Evidence ID": step_name,
                    "Tool": "FileReader",
                    "File": file_path,
                    "Content Length": f"{len(result)} characters"
                }
            )
    else:
        raise ValueError(f"Unknown tool: {tool}")

    _results[step_name] = str(result)
    return {"results": _results}