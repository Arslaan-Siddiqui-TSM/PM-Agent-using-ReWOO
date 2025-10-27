from states.rewoo_state import ReWOO

from app.graph import get_graph
from utils.helper import MarkdownLogger, set_global_logger
from core.document_intelligence_pipeline import DocumentIntelligencePipeline

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
import time
import os
import glob


def run_agent(task: str = "Create implementation plan for the client project.", 
              use_document_intelligence: bool = True,
              enable_cache: bool = True):
    """
    Run the ReWOO agent with all documents in the files directory.
    
    The agent will automatically load:
    - All PDF documents from the 'files/' directory
    - Optionally process through Document Intelligence Pipeline (recommended)
    - Feasibility question answers from 'outputs/feasibility_assessment.md'
    
    All execution steps will be saved to a markdown file in outputs/ directory.
    
    Args:
        task (str): Task description for the agent
        use_document_intelligence (bool): Use intelligent document processing (recommended)
        enable_cache (bool): Enable caching for faster repeated runs
    """
    start_time = time.time()
    
    # Get list of all PDF files in the files directory
    files_dir = os.path.join(os.path.dirname(__file__), "files")
    pdf_files = glob.glob(os.path.join(files_dir, "*.pdf"))
    
    # Initialize markdown logger
    md_logger = MarkdownLogger(output_dir="outputs")
    md_logger.start(task, pdf_files, "outputs/feasibility_assessment.md")
    
    # Set as global logger so other modules can access it
    set_global_logger(md_logger)
    
    # Process documents with intelligence pipeline (NEW)
    document_context = None
    if use_document_intelligence:
        console = Console()
        console.print("\n[bold yellow]🧠 Using Document Intelligence Pipeline[/bold yellow]")
        console.print("[dim]This will automatically classify, extract, and analyze documents...[/dim]\n")
        
        pipeline = DocumentIntelligencePipeline(enable_cache=enable_cache, verbose=True)
        pipeline_result = pipeline.process_documents(pdf_files, output_dir="outputs/intermediate")
        
        # Generate comprehensive planning context
        document_context = pipeline.get_planning_context(pipeline_result)
        
        console.print("\n[green]✓ Document Intelligence Pipeline completed[/green]")
        console.print(f"[dim]Analysis report saved to: outputs/intermediate/document_analysis_report.md[/dim]\n")
    else:
        console = Console()
        console.print("\n[yellow]⚠️  Document Intelligence Pipeline disabled - using legacy mode[/yellow]\n")
    
    console = Console()
    console.rule("[bold blue]🔍 Executing ReWOO Reasoning Graph[/bold blue]")
    console.print(f"[bold cyan]🟡 Processing {len(pdf_files)} documents from files/ directory:[/bold cyan]")
    for pdf_file in sorted(pdf_files):
        console.print(f"   • {os.path.basename(pdf_file)}")
    console.print(f"[bold cyan]📋 Task:[/bold cyan] {task}")
    console.print(f"[bold cyan]💡 Feasibility Context:[/bold cyan] outputs/feasibility_assessment.md")
    if use_document_intelligence:
        console.print(f"[bold cyan]🧠 Document Intelligence:[/bold cyan] ENABLED")
    console.print("\n")
    
    # Create initial state with document context
    initial_state = ReWOO(
        task=task,
        plan_string=None,
        result=None,
        document_context=document_context
    )
    
    app = get_graph(initial_state)
    final_state = None

    for s in app.stream(initial_state):
        # Each s is a dict like {'plan': {...}} or {'tool': {...}} etc.
        node_name = next(iter(s))
        data = s[node_name]

        if node_name == "plan":
            console.rule("[bold magenta]🧩 Planning Stage[/bold magenta]")
            console.print(Panel.fit(data["plan_string"], title="Generated Plan", border_style="magenta"))
            
            # Log to markdown
            md_logger.log_planning_stage(data["plan_string"], data.get("steps", []))
            
            if data["steps"]:
                table = Table(title="Parsed Plan Steps", box=box.ROUNDED)
                table.add_column("Step", style="bold cyan")
                table.add_column("Evidence ID", style="bold yellow")
                table.add_column("Tool", style="bold green")
                table.add_column("Input", style="dim")

                for idx, (plan_text, step_name, tool, tool_input) in enumerate(data["steps"], 1):
                    table.add_row(str(idx), step_name, tool, tool_input.strip())
                console.print(table)
        
        elif node_name == "tool":
            console.rule("[bold green]🔧 Tool Execution[/bold green]")
            results = data.get("results", {})
            
            # Log to markdown
            md_logger.log_tool_execution(results)
            
            if results:
                for k, v in results.items():
                    console.print(Panel(str(v), title=f"Result of {k}", border_style="green"))
            else:
                console.print("[yellow]No results yet.[/yellow]")
        
        elif node_name == "solve":
            console.rule("[bold cyan]🧠 Final Solution[/bold cyan]")
            console.print(Panel(str(data["result"]).strip(), title="Final Answer", border_style="cyan"))
            
            # Log to markdown
            md_logger.log_final_solution(str(data["result"]))
        
        else:
            console.print(Panel(f"Unknown state: {node_name}", border_style="red"))
        
        console.print("\n")
        final_state = s

    console.rule("[bold blue]✅ Finished Execution[/bold blue]")
    if final_state and "solve" in final_state:
        console.print(Panel(Text(final_state["solve"]["result"], justify="center", style="bold white on blue1"),
                            title="Final Result", border_style="blue", expand=False))
    
    elapsed_time = time.time() - start_time
    console.print(f"\n[bold green]⏱️ Total execution time: {elapsed_time:.2f} seconds[/bold green]")
    
    # Finalize and save markdown log
    log_filepath = md_logger.finalize(elapsed_time)
    console.print(f"[bold yellow]📝 Execution log saved to: {log_filepath}[/bold yellow]")


if __name__ == "__main__":
    # The agent will automatically process all PDF files in the files/ directory
    # 
    # NEW: Document Intelligence Pipeline (Recommended)
    # - Automatically classifies documents by type (not based on filename)
    # - Extracts structured information from each document
    # - Analyzes for gaps, conflicts, and planning readiness
    # - Generates comprehensive planning context
    # - Uses caching for faster subsequent runs
    #
    # Set use_document_intelligence=False to use legacy raw document loading
    
    run_agent(
        task="Create implementation plan for the client project.",
        use_document_intelligence=True,  # Use intelligent document processing
        enable_cache=True  # Enable caching for faster runs
    )