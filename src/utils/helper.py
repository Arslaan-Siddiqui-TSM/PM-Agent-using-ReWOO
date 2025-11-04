import os
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
        self.logs.append("# Reflection Agent Execution Log\n")
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
    
    def log_iteration_draft(
        self,
        iteration_index: int,
        draft_text: str,
        revision_focus: Optional[str] = None,
        context_source: Optional[str] = None,
    ):
        """Log the drafted plan for the given iteration."""

        self.logs.append(f"## � Iteration {iteration_index}: Draft\n\n")
        if context_source or revision_focus:
            self.logs.append("### Context\n\n")
            if context_source:
                self.logs.append(f"- **Context Source:** {context_source}\n")
            if revision_focus:
                self.logs.append(f"- **Revision Focus:** {revision_focus}\n")
            self.logs.append("\n")

        self.logs.append("### Draft Plan\n\n")
        self.logs.append("```\n")
        self.logs.append(draft_text)
        self.logs.append("\n```\n\n")
        self.logs.append("---\n\n")

    def log_iteration_critique(self, iteration_index: int, critique_text: str):
        """Log the critique produced for the current draft."""

        self.logs.append(f"## 🔍 Iteration {iteration_index}: Critique\n\n")
        self.logs.append("```\n")
        self.logs.append(critique_text)
        self.logs.append("\n```\n\n")
        self.logs.append("---\n\n")

    def log_revision_decision(
        self,
        iteration_index: int,
        decision: str,
        rationale: Optional[str],
        required_actions: Optional[str],
    ):
        """Log the outcome of the revise step."""

        self.logs.append(f"## ♻️ Iteration {iteration_index}: Revision Decision\n\n")
        self.logs.append(f"- **Decision:** {decision}\n")
        if rationale:
            self.logs.append(f"- **Rationale:** {rationale}\n")
        if required_actions:
            self.logs.append("- **Required Actions:**\n")
            for line in required_actions.splitlines():
                cleaned = line.strip()
                if cleaned:
                    self.logs.append(f"  - {cleaned}\n")
        if not required_actions:
            self.logs.append("- **Required Actions:** None\n")
        self.logs.append("\n---\n\n")

    def log_final_plan(self, plan: str):
        """Log the final accepted plan."""

        self.logs.append("## ✅ Final Project Plan\n\n")
        self.logs.append("```\n")
        plan_text = plan.strip()
        if len(plan_text) > 4000:
            plan_text = plan_text[:4000] + "\n... [truncated - see iteration logs for full content] ..."
        self.logs.append(plan_text)
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


