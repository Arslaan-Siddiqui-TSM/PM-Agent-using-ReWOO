import os
from states.rewoo_state import ReWOO
from datetime import datetime
from typing import Optional


# Global logger instance that can be accessed from any module
_global_logger = None


def set_global_logger(logger):
    """Set the global logger instance."""
    global _global_logger
    _global_logger = logger


def get_global_logger():
    """Get the global logger instance."""
    return _global_logger


class MarkdownLogger:
    """Utility class to capture and save agent execution steps to markdown file."""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self.logs = []
        self.start_time = None
        self.end_time = None
        self.llm_call_count = 0
        
    def start(self, task: str, pdf_files: list, feasibility_file: str):
        """Log the start of agent execution."""
        self.start_time = datetime.now()
        self.logs.append("# ReWOO Agent Execution Log\n")
        self.logs.append(f"**Execution Date:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        self.logs.append("---\n\n")
        self.logs.append("## Configuration\n\n")
        self.logs.append(f"**Task:** {task}\n\n")
        self.logs.append(f"**Documents Processed ({len(pdf_files)}):**\n")
        for pdf_file in sorted(pdf_files):
            self.logs.append(f"- {os.path.basename(pdf_file)}\n")
        self.logs.append(f"\n**Feasibility Context:** `{feasibility_file}`\n\n")
        self.logs.append("---\n\n")
    def log_llm_interaction(self, stage: str, prompt: str, response: str, additional_context: Optional[dict] = None):
        """Log complete LLM prompt and response.
        
        Args:
            stage (str): The stage of execution (e.g., "Planning", "Tool Execution - LLM", "Solver")
            prompt (str): The complete prompt sent to the LLM
            response (str): The complete response from the LLM
            additional_context (dict): Any additional context to log (e.g., tool name, evidence ID)
        """
        self.llm_call_count += 1
        self.logs.append(f"## 🤖 LLM Interaction #{self.llm_call_count}: {stage}\n\n")
        
        if additional_context:
            self.logs.append("### Context\n\n")
            for key, value in additional_context.items():
                self.logs.append(f"- **{key}:** {value}\n")
            self.logs.append("\n")
        
        self.logs.append("### Complete Prompt Sent to LLM\n\n")
        self.logs.append("```\n")
        self.logs.append(prompt)
        self.logs.append("\n```\n\n")
        
        self.logs.append("### LLM Response\n\n")
        self.logs.append("```\n")
        self.logs.append(str(response))
        self.logs.append("\n```\n\n")
        self.logs.append("---\n\n")
    
    def log_planning_stage(self, plan_string: str, steps: list):
        """Log the planning stage output."""
        self.logs.append("## 🧩 Planning Stage Summary\n\n")
        self.logs.append("### Generated Plan\n\n")
        self.logs.append("```\n")
        self.logs.append(plan_string)
        self.logs.append("\n```\n\n")
        
        if steps:
            self.logs.append("### Parsed Plan Steps\n\n")
            self.logs.append("| Step | Evidence ID | Tool | Input |\n")
            self.logs.append("|------|-------------|------|-------|\n")
            for idx, (plan_text, step_name, tool, tool_input) in enumerate(steps, 1):
                # Escape pipe characters in table cells
                input_escaped = tool_input.strip().replace("|", "\\|")
                self.logs.append(f"| {idx} | {step_name} | {tool} | {input_escaped} |\n")
            self.logs.append("\n")
        
        self.logs.append("---\n\n")
    
    def log_tool_execution(self, results: dict):
        """Log the tool execution results summary."""
        self.logs.append("## 🔧 Tool Execution Summary\n\n")
        
        if results:
            for k, v in results.items():
                self.logs.append(f"### Result of {k}\n\n")
                self.logs.append("```\n")
                result_text = str(v)
                # Truncate very long results for summary section
                if len(result_text) > 2000:
                    result_text = result_text[:2000] + "\n... [truncated - see LLM interaction details above for full content] ..."
                self.logs.append(result_text)
                self.logs.append("\n```\n\n")
        else:
            self.logs.append("*No results yet.*\n\n")
        
        self.logs.append("---\n\n")
    
    def log_final_solution(self, result: str):
        """Log the final solution summary."""
        self.logs.append("## 🧠 Final Solution Summary\n\n")
        self.logs.append("```\n")
        result_text = str(result).strip()
        # Truncate if very long for summary
        if len(result_text) > 3000:
            result_text = result_text[:3000] + "\n... [truncated - see Solver LLM interaction above for full content] ..."
        self.logs.append(result_text)
        self.logs.append("\n```\n\n")
        self.logs.append("---\n\n")
    
    def finalize(self, elapsed_time: float) -> str:
        """Finalize the log and save to file."""
        self.end_time = datetime.now()
        
        self.logs.append("## ✅ Execution Summary\n\n")
        if self.start_time:
            self.logs.append(f"**Start Time:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        else:
            self.logs.append(f"**Start Time:** Not recorded\n\n")
        self.logs.append(f"**End Time:** {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        self.logs.append(f"**Total Execution Time:** {elapsed_time:.2f} seconds\n\n")
        self.logs.append(f"**Total LLM Calls:** {self.llm_call_count}\n\n")
        
        # Save to file
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S") if self.start_time else datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agent_execution_log_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(self.logs)
        
        return filepath


def load_prompt_template(path: str) -> str:
    """
    Load a prompt template from a file.

    Args:
        path (str): The path to the prompt template file.
    Returns:
        str: The content of the prompt template file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_current_task(state: ReWOO):
    """Get the current task number for the given state.

    Args:
        state (ReWOO): The current state of the ReWOO agent.

    Returns:
        int | None: The current task number, or None if all tasks are completed.
    """
    if not hasattr(state, "results") or state.results is None:
        return 1
    if state.steps is not None and len(state.results) == len(state.steps):
        return None
    else:
        return len(state.results) + 1


def route(state):
    """Determine the next node to route to based on the current task state.

    Args:
        state (ReWOO): The current state of the ReWOO agent.

    Returns:
        str: The name of the next node to route to ("solve" or "tool").
    """
    _step = get_current_task(state)
    if _step is None:
        # We have executed all tasks
        return "solve"
    else:
        # We are still executing tasks, loop back to the "tool" node
        return "tool"
    
def truncate_query(query: str, max_length: int = 400) -> str:
    """Truncate a search query to fit within the maximum length while preserving meaning."""
    if len(query) <= max_length:
        return query

    # If query is too long, try to find a good breaking point
    # Look for sentence endings or common separators
    separators = ['. ', '! ', '? ', '; ', ', ', ' - ']

    for separator in separators:
        parts = query.split(separator)
        if len(parts) > 1:
            # Try to fit as much as possible
            result = ""
            for part in parts[:-1]:  # All parts except the last
                if len(result + part + separator.strip()) <= max_length - 50:  # Leave room for closing
                    result += part + separator.strip() + ' '
                else:
                    break

            # Add a shortened version of the last part if there's room
            remaining = max_length - len(result) - 10
            if remaining > 50:  # Only add if we have reasonable space
                last_part = parts[-1][:remaining] + "..."
                result += last_part
            else:
                result = result.rstrip() + "..."

            return result[:max_length]

    # If no good separators found, just truncate with ellipsis
    return query[:max_length-3] + "..."


def load_feasibility_answers(file_path="outputs/feasibility_questions.md"):
    """Reads feasibility answers (if provided by Tech Lead) from markdown file."""
    if not os.path.exists(file_path):
        print(f"⚠️ Feasibility answers file not found at {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    return content


def load_all_documents_from_directory(directory_path: str) -> str:
    """Load and extract text from all PDF files in the specified directory.
    
    Args:
        directory_path (str): Path to the directory containing PDF files.
        
    Returns:
        str: Combined text content from all PDF documents with file separators.
    """
    import glob
    try:
        import fitz
    except ImportError:
        import pymupdf as fitz
    
    pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
    
    if not pdf_files:
        return "No PDF files found in the specified directory."
    
    all_content = []
    
    for pdf_path in sorted(pdf_files):  # Sort for consistent ordering
        filename = os.path.basename(pdf_path)
        try:
            with fitz.open(pdf_path) as doc:
                text = ""
                for page in doc:
                    page_text = page.get_text("text")
                    text += str(page_text)
                
                all_content.append(f"=== Document: {filename} ===\n{text.strip()}\n")
        except Exception as e:
            all_content.append(f"=== Document: {filename} ===\n[Error reading file: {str(e)}]\n")
    
    return "\n\n".join(all_content)

