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
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Starting PDF text extraction from {len(file_paths)} files")
    all_text = ""
    for file_path in file_paths:
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Processing file: {file_path}")
        try:
            with fitz.open(file_path) as doc:
                console.print(f"[bold yellow]DEBUG:[/bold yellow] Document opened successfully, pages: {len(doc)}")
                page_num = 0
                for page in doc:
                    page_num += 1
                    page_text = page.get_text("text")
                    console.print(f"[bold yellow]DEBUG:[/bold yellow] Page {page_num}: extracted {len(str(page_text))} characters")
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
                console.print(f"[bold yellow]DEBUG:[/bold yellow] Finished processing {file_path}: total characters so far: {len(all_text)}")
        except Exception as e:
            console.print(f"[bold red]DEBUG ERROR:[/bold red] Failed to read {file_path}: {e}")
            all_text += f"\n[Error reading {file_path}: {e}]\n"
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Total extracted text length: {len(all_text)} characters")
    return all_text.strip()


def generate_feasibility_questions(document_text: str) -> str:
    """Generate feasibility questions for the Tech Lead review.

    Args:
        document_text (str): The text content of the document.

    Returns:
        str: The generated feasibility assessment in markdown format.
    """    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Starting feasibility question generation")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Input document text length: {len(document_text)} characters")
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "feasibility_prompt.txt")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Loading prompt from: {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        feasibility_prompt = f.read()
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Prompt template loaded, length: {len(feasibility_prompt)} characters")
    
    # # Limit document text to avoid token limits
    # truncated_text = document_text[:8000]
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Truncating document text to {len(document_text)} characters")
    
    feasibility_prompt = feasibility_prompt.format(document_text=document_text)
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Final prompt length: {len(feasibility_prompt)} characters")
    
    # Show a preview of the prompt
    console.print("\n[bold magenta]DEBUG - PROMPT PREVIEW:[/bold magenta]")
    console.print("[dim]" + "="*80 + "[/dim]")
    console.print(f"[cyan]Number of character in prompt: {len(feasibility_prompt)}[/cyan]")
    console.print("[dim]" + "="*80 + "[/dim]\n")
    
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Invoking LLM model...")
    
    try:
        result = model.invoke(feasibility_prompt)
        console.print(f"[bold green]DEBUG:[/bold green] LLM invocation successful")
        console.print(f"[bold yellow]DEBUG:[/bold yellow] Result type: {type(result)}")
    except Exception as e:
        console.print(f"[bold red]DEBUG ERROR:[/bold red] LLM invocation failed: {e}")
        return f"Error calling LLM: {e}"

    # Normalize result to a string so callers (like save_questions_to_markdown) always receive str
    content = getattr(result, "content", result)
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Content type: {type(content)}")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Content length: {len(str(content))} characters")
    
    # Show a preview of the LLM response
    console.print("\n[bold magenta]DEBUG - LLM RESPONSE PREVIEW:[/bold magenta]")
    console.print("[dim]" + "="*80 + "[/dim]")
    content_str = str(content)
    response_preview = content_str[:800] + "\n\n... [truncated] ...\n\n" + content_str[-300:] if len(content_str) > 1100 else content_str
    console.print(f"[green]{response_preview}[/green]")
    console.print("[dim]" + "="*80 + "[/dim]\n")

    if isinstance(content, str):
        console.print(f"[bold green]DEBUG:[/bold green] Returning string content")
        return content

    # If it's a list or dict or other object, convert to a readable JSON or fallback to str()
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Converting non-string content to JSON")
    try:
        import json
        json_result = json.dumps(content, ensure_ascii=False, indent=2)
        console.print(f"[bold green]DEBUG:[/bold green] JSON conversion successful")
        return json_result
    except Exception:
        console.print(f"[bold yellow]DEBUG:[/bold yellow] JSON conversion failed, using str()")
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
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Saving questions to markdown")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Input content length: {len(questions_md)} characters")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] File name: {file_name}")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Output directory: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    # Derive a sane base name from the provided file path
    base = os.path.splitext(os.path.basename(file_name))[0]
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Base filename: {base}")
    
    output_path = os.path.join(output_dir, f"{base}.md")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Full output path: {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(questions_md)
    
    console.print(f"[bold green]DEBUG:[/bold green] File written successfully")
    return output_path


def run_feasibility_agent(file_paths: list[str]) -> str:
    """Run the feasibility agent on multiple documents, producing a single markdown file."""
    console.print(f"[bold yellow]DEBUG:[/bold yellow] === Starting Feasibility Agent ===")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Received {len(file_paths)} file paths")
    
    if not file_paths:
        console.print(Panel("No files provided for feasibility analysis.", border_style="yellow"))
        console.print(f"[bold red]DEBUG:[/bold red] Exiting early - no files provided")
        return ""

    for i, fp in enumerate(file_paths, 1):
        console.print(f"[bold yellow]DEBUG:[/bold yellow] File {i}: {fp}")

    console.rule("[bold blue]🔍 Feasibility Agent[/bold blue]")
    console.print(f"[bold cyan]Reading {len(file_paths)} project document(s)...[/bold cyan]")

    # Combine text from all documents
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Calling extract_text_from_pdfs...")
    docs_text = extract_text_from_pdfs(file_paths)
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Text extraction complete")
    console.print(Panel(f"Extracted [bold]{len(docs_text)}[/bold] characters from all documents.", border_style="cyan"))

    # Generate assessment once for all documents combined
    console.print(Panel("Generating feasibility questions...", border_style="magenta"))
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Calling generate_feasibility_questions...")
    questions_md = generate_feasibility_questions(docs_text)
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Question generation complete")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Generated content length: {len(questions_md)} characters")

    # Save into a single file
    console.print(f"[bold yellow]DEBUG:[/bold yellow] Calling save_questions_to_markdown...")
    output_path = save_questions_to_markdown(questions_md, "feasibility_assessment.md")
    console.print(f"[bold yellow]DEBUG:[/bold yellow] File save complete")
    console.print(Panel(f"Feasibility file saved to: [bold]{output_path}[/bold]", border_style="green"))

    console.print(Panel(Text("Feasibility stage complete. Please review and fill in answers before proceeding.",
                             justify="center"), border_style="green"))
    console.print(f"[bold yellow]DEBUG:[/bold yellow] === Feasibility Agent Complete ===")
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
