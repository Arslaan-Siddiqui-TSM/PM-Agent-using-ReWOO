#!/usr/bin/env python3
"""
Test script to demonstrate beautiful token tracking for LLM calls.
"""

from src.config.llm_config import model, session_tracker
from rich.console import Console

console = Console()

def main():
    console.print("\n[bold cyan]═══ Testing Beautiful Token Tracking ═══[/bold cyan]\n")
    
    # Test 1: Simple query
    console.print("[yellow]Test 1: Simple greeting[/yellow]")
    response1 = model.invoke("Say hello in a creative way!")
    console.print(f"[dim]Response: {response1.content[:100]}...[/dim]\n")
    
    # Test 2: Medium-sized query
    console.print("[yellow]Test 2: Technical explanation[/yellow]")
    response2 = model.invoke(
        "Explain what LangChain is in 2-3 sentences."
    )
    console.print(f"[dim]Response: {response2.content[:100]}...[/dim]\n")
    
    # Test 3: Larger query
    console.print("[yellow]Test 3: Code generation[/yellow]")
    response3 = model.invoke(
        "Write a Python function that calculates the Fibonacci sequence up to n terms."
    )
    console.print(f"[dim]Response: {response3.content[:100]}...[/dim]\n")
    
    # Test 4: Query without token display
    console.print("[yellow]Test 4: Silent call (no token display)[/yellow]")
    response4 = model.invoke("What is 2+2?", show_tokens=False)
    console.print(f"[dim]Response: {response4.content}[/dim]\n")
    
    # Display session summary
    console.print("\n[bold magenta]═══ Session Complete ═══[/bold magenta]\n")
    session_tracker.print_summary()


if __name__ == "__main__":
    main()

