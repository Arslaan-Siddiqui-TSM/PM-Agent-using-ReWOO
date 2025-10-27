import os
import fitz
from config.llm_config import model
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()


def extract_text_from_pdfs(file_paths: list[str]) -> str:
    """Extract text from a list of PDF files.

    Args:
        file_paths (list[str]): List of paths to the PDF files.

    Returns:
        str: The extracted text from all PDF files.
    """
    all_text = ""
    for file_path in file_paths:
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    page_text = page.get_text("text")
                    if isinstance(page_text, str):
                        all_text += page_text + "\n"
                    elif isinstance(page_text, list):
                        # join list elements safely
                        all_text += "\n".join(map(str, page_text)) + "\n"
                    elif isinstance(page_text, dict):
                        # fallback for dict-style returns
                        all_text += str(page_text) + "\n"
                    else:
                        # catch-all coercion
                        all_text += str(page_text) + "\n"
        except Exception as e:
            all_text += f"\n[Error reading {file_path}: {e}]\n"
    return all_text.strip()


def generate_feasibility_questions(document_text: str) -> str:
    """Generate feasibility questions for the Tech Lead review.

    Args:
        document_text (str): The text content of the document.

    Returns:
        str: The generated feasibility assessment in markdown format.
    """    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "feasibility_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        feasibility_prompt = f.read()
    # Limit document text to avoid token limits
    truncated_text = document_text[:8000]
    feasibility_prompt = feasibility_prompt.format(document_text=truncated_text)
    try:
        result = model.invoke(feasibility_prompt)
    except Exception as e:
        return f"Error calling LLM: {e}"

    # Normalize result to a string so callers (like save_questions_to_markdown) always receive str
    content = getattr(result, "content", result)

    if isinstance(content, str):
        return content

    # If it's a list or dict or other object, convert to a readable JSON or fallback to str()
    try:
        import json
        return json.dumps(content, ensure_ascii=False, indent=2)
    except Exception:
        return str(content)


def save_questions_to_markdown(questions_md: str, file_name: str, output_dir="outputs"):
    """Save feasibility questions to a markdown file.

    Args:
        questions_md (str): The markdown content to save.
        file_name (str): The base name for the output file (without extension).
        output_dir (str, optional): The directory to save the output file. Defaults to "outputs".

    Returns:
        str: The path to the saved markdown file.
    """    
    os.makedirs(output_dir, exist_ok=True)
    # Derive a sane base name from the provided file path
    base = os.path.splitext(os.path.basename(file_name))[0]
    output_path = os.path.join(output_dir, f"{base}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(questions_md)
    return output_path


def run_feasibility_agent(file_paths: list[str]) -> str:
    """Run the feasibility agent on multiple documents, producing a single markdown file."""
    if not file_paths:
        console.print(Panel("No files provided for feasibility analysis.", border_style="yellow"))
        return ""

    console.rule("[bold blue]🔍 Feasibility Agent[/bold blue]")
    console.print(f"[bold cyan]Reading {len(file_paths)} project document(s)...[/bold cyan]")

    # Combine text from all documents
    docs_text = extract_text_from_pdfs(file_paths)
    console.print(Panel(f"Extracted [bold]{len(docs_text)}[/bold] characters from all documents.", border_style="cyan"))

    # Generate assessment once for all documents combined
    console.print(Panel("Generating feasibility questions...", border_style="magenta"))
    questions_md = generate_feasibility_questions(docs_text)

    # Save into a single file
    output_path = save_questions_to_markdown(questions_md, "feasibility_assessment.md")
    console.print(Panel(f"Feasibility file saved to: [bold]{output_path}[/bold]", border_style="green"))

    console.print(Panel(Text("Feasibility stage complete. Please review and fill in answers before proceeding.",
                             justify="center"), border_style="green"))
    return output_path



if __name__ == "__main__":
    # Example usage - automatically reads all PDF files from the files directory
    import glob
    files_dir = "files"
    sample_files = glob.glob(os.path.join(files_dir, "*.pdf"))
    
    if not sample_files:
        console.print(f"[bold yellow]No PDF files found in {files_dir} directory[/bold yellow]")
    else:
        console.print(f"[bold cyan]Found {len(sample_files)} PDF files to process[/bold cyan]")
        questions_file = run_feasibility_agent(sample_files)
