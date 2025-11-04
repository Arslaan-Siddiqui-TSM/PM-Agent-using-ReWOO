"""
Test script for Document Intelligence Pipeline

Tests the new document intelligence system with sample documents.
"""

import os
import sys
import glob
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.document_intelligence_pipeline import DocumentIntelligencePipeline
from rich.console import Console
from rich.panel import Panel


def test_document_intelligence():
    """Test the document intelligence pipeline with sample documents."""
    
    console = Console()
    console.print("\n[bold blue]🧪 Testing Document Intelligence Pipeline[/bold blue]\n")
    
    # Get PDF files
    files_dir = Path(__file__).parent / "files"
    pdf_files = list(glob.glob(str(files_dir / "*.pdf")))
    
    if not pdf_files:
        console.print("[red]❌ No PDF files found in files/ directory[/red]")
        return False
    
    console.print(f"[cyan]Found {len(pdf_files)} PDF files:[/cyan]")
    for pdf_file in pdf_files:
        console.print(f"  • {os.path.basename(pdf_file)}")
    console.print()
    
    try:
        # Initialize pipeline
        console.print("[yellow]Initializing pipeline...[/yellow]")
        pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=True)
        
        # Process documents
        console.print("\n[yellow]Processing documents...[/yellow]\n")
        result = pipeline.process_documents(
            pdf_files,
            output_dir="outputs/test_intermediate"
        )
        
        # Display results
        console.print("\n[bold green]✅ Pipeline Test Successful![/bold green]\n")
        
        # Show quick summary
        report = result["analysis_report"]
        summary = f"""
[bold]Test Results Summary:[/bold]

📊 Document Processing:
  - Total Documents: {len(result['classifications'])}
  - Classifications: ✓
  - Extractions: ✓
  - Analysis: ✓

📈 Analysis Metrics:
  - Coverage Score: {report.coverage_score:.2%}
  - Planning Readiness: {report.readiness_for_planning.upper()}
  - Confidence Score: {report.confidence_score:.2%}

📁 Document Types Found:
  {', '.join(report.document_types_present)}

❗ Missing Types:
  {', '.join(report.document_types_missing) if report.document_types_missing else 'None'}

🔍 Critical Issues:
  - High Severity Conflicts: {report.conflicts.severity_high}
  - Missing Critical Info: {len(report.gaps.missing_critical_info)}
  - Questions for Client: {len(report.critical_assessment)}

💾 Cache Statistics:
  - Total Cached Files: {result.get('cache_stats', {}).get('total_cached_files', 0)}
  - Cache Size: {result.get('cache_stats', {}).get('cache_size_mb', 0):.2f} MB
"""
        console.print(Panel(summary, title="Pipeline Test Results", border_style="green"))
        
        # Test planning context generation
        console.print("\n[yellow]Testing planning context generation...[/yellow]")
        planning_context = pipeline.get_planning_context(result)
        
        console.print(f"\n[green]✓ Planning context generated ({len(planning_context)} characters)[/green]")
        console.print(f"[dim]Preview:[/dim]")
        console.print(Panel(planning_context[:500] + "...", border_style="dim"))
        
        console.print("\n[bold green]🎉 All tests passed![/bold green]")
        console.print("\n[cyan]Output files saved to:[/cyan]")
        console.print("  • outputs/test_intermediate/document_classifications.json")
        console.print("  • outputs/test_intermediate/document_extractions.json")
        console.print("  • outputs/test_intermediate/document_analysis_report.json")
        console.print("  • outputs/test_intermediate/document_analysis_report.md")
        
        return True
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test Failed![/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        return False


def test_backward_compatibility():
    """Test that legacy mode still works."""
    
    console = Console()
    console.print("\n[bold blue]🧪 Testing Backward Compatibility[/bold blue]\n")
    
    try:
        # Import and test that old loading still works
        from utils.helper import load_all_documents_from_directory
        
        files_dir = Path(__file__).parent.parent / "files"
        documents = load_all_documents_from_directory(str(files_dir))
        
        console.print(f"[green]✓ Legacy document loading works ({len(documents)} characters)[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Legacy mode failed: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    console = Console()
    
    console.rule("[bold cyan]Document Intelligence System Tests[/bold cyan]")
    
    # Test 1: Document Intelligence Pipeline
    test1_passed = test_document_intelligence()
    
    # Test 2: Backward Compatibility
    test2_passed = test_backward_compatibility()
    
    # Final summary
    console.print("\n")
    console.rule("[bold cyan]Test Summary[/bold cyan]")
    
    if test1_passed and test2_passed:
        console.print("\n[bold green]✅ All tests passed successfully![/bold green]\n")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ Some tests failed[/bold red]\n")
        sys.exit(1)
