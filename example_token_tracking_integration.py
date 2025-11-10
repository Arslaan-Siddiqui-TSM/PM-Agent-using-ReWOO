#!/usr/bin/env python3
"""
Example: Integrating Token Tracking into Existing Scripts

This script demonstrates how to add token tracking to your existing
PM-Agent workflows with minimal changes.
"""

from src.config.llm_config import model
from src.utils import enable_auto_summary
from rich.console import Console

console = Console()

def main():
    # Enable automatic session summary when script exits
    enable_auto_summary()
    
    console.print("\n[bold cyan]═══ PM-Agent with Token Tracking ═══[/bold cyan]\n")
    
    # Simulate a feasibility analysis workflow
    console.print("[bold yellow]Step 1:[/bold yellow] Analyzing project requirements...")
    
    requirements_prompt = """
    Analyze the following project requirements:
    - E-commerce platform for apparel
    - Support 100 concurrent users
    - Stripe payment integration
    - Order tracking and management
    
    Provide a brief feasibility assessment.
    """
    
    analysis = model.invoke(requirements_prompt)
    console.print(f"[green]✓ Analysis complete[/green]\n")
    
    # Simulate generating questions
    console.print("[bold yellow]Step 2:[/bold yellow] Generating feasibility questions...")
    
    questions_prompt = """
    Based on an e-commerce apparel platform, generate 3 critical
    technical questions that need to be answered for feasibility.
    """
    
    questions = model.invoke(questions_prompt)
    console.print(f"[green]✓ Questions generated[/green]\n")
    
    # Simulate risk assessment
    console.print("[bold yellow]Step 3:[/bold yellow] Assessing risks...")
    
    risk_prompt = """
    List 3 major technical risks for building an e-commerce platform
    with payment integration and high concurrency requirements.
    Be concise.
    """
    
    risks = model.invoke(risk_prompt)
    console.print(f"[green]✓ Risk assessment complete[/green]\n")
    
    console.print("[bold green]═══ Workflow Complete ═══[/bold green]\n")
    console.print("[dim]Session summary will be displayed automatically...[/dim]\n")
    
    # Session summary will be displayed automatically when script exits
    # because we called enable_auto_summary() at the start


def example_manual_summary():
    """Example showing manual summary display."""
    from src.utils import print_summary, reset_tracker
    
    console.print("\n[bold cyan]═══ Manual Summary Example ═══[/bold cyan]\n")
    
    # Make some calls
    for i in range(3):
        console.print(f"[yellow]Call {i+1}[/yellow]")
        model.invoke(f"Say something interesting about number {i+1}")
    
    # Manually display summary
    console.print("\n[bold yellow]Displaying manual summary:[/bold yellow]\n")
    print_summary()
    
    # Reset for next workflow
    reset_tracker()


def example_programmatic_access():
    """Example showing programmatic access to token stats."""
    from src.utils import get_session_stats
    
    console.print("\n[bold cyan]═══ Programmatic Access Example ═══[/bold cyan]\n")
    
    # Make a call
    model.invoke("Explain quantum computing in one sentence", show_tokens=False)
    
    # Get stats programmatically
    stats = get_session_stats()
    
    console.print("\n[bold magenta]Custom Stats Display:[/bold magenta]")
    console.print(f"  Calls made: {stats['total_calls']}")
    console.print(f"  Total tokens: {stats['total_tokens']:,}")
    console.print(f"  Duration: {stats['session_duration']:.2f}s\n")


if __name__ == "__main__":
    # Run the main workflow
    main()
    
    # Uncomment to try other examples:
    # example_manual_summary()
    # example_programmatic_access()

