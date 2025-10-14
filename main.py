from states.rewoo_state import ReWOO

from app.graph import get_graph

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

task = "Create a complete project plan in Markdown format based on the BRD document located at 'files/brd_1.pdf'."


if __name__ == "__main__":
    app = get_graph(ReWOO(task=task, plan_string=None, result=None))
    # === Improved Output Formatting ===
    console = Console()
    final_state = None

    console.rule("[bold blue]🔍 Executing ReWOO Reasoning Graph[/bold blue]")

    for s in app.stream(ReWOO(task=task, plan_string=None, result=None)):
        # Each s is a dict like {'plan': {...}} or {'tool': {...}} etc.
        node_name = next(iter(s))
        data = s[node_name]

        if node_name == "plan":
            console.rule("[bold magenta]🧩 Planning Stage[/bold magenta]")
            console.print(Panel.fit(data["plan_string"], title="Generated Plan", border_style="magenta"))
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
            if results:
                for k, v in results.items():
                    console.print(Panel(str(v), title=f"Result of {k}", border_style="green"))
            else:
                console.print("[yellow]No results yet.[/yellow]")
        
        elif node_name == "solve":
            console.rule("[bold cyan]🧠 Final Solution[/bold cyan]")
            console.print(Panel(str(data["result"]).strip(), title="Final Answer", border_style="cyan"))
        
        else:
            console.print(Panel(f"Unknown state: {node_name}", border_style="red"))
        
        console.print("\n")
        final_state = s

    console.rule("[bold blue]✅ Finished Execution[/bold blue]")
    if final_state and "solve" in final_state:
        console.print(Panel(Text(final_state["solve"]["result"], justify="center", style="bold white on chartreuse3"),
                            title="Final Result", border_style="blue", expand=False))
