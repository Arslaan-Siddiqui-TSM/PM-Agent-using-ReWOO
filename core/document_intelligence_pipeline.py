"""
Document Intelligence Pipeline

Orchestrates the document classification, extraction, and analysis process.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from agents.document_classifier import DocumentClassifierAgent, DocumentClassification
from agents.content_extractor import ContentExtractorAgent, ExtractedContent
from core.document_analyzer import DocumentAnalyzer, DocumentAnalysisReport
from core.cache_manager import CacheManager
from config.document_intelligence_config import (
    CLASSIFICATION_CONFIG,
    EXTRACTION_CONFIG,
    ANALYSIS_CONFIG,
    PROCESSING_CONFIG
)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class DocumentIntelligencePipeline:
    """
    Main pipeline for processing documents with intelligence.
    
    Workflow:
    1. Classify documents (with caching)
    2. Extract structured content (with caching)
    3. Analyze document set for gaps, conflicts, and readiness
    4. Generate comprehensive context for planning
    """
    
    def __init__(
        self,
        llm=None,
        enable_cache: bool = True,
        cache_dir: Optional[str] = None,
        verbose: bool = True
    ):
        """
        Initialize the pipeline.
        
        Args:
            llm: Language model to use (defaults to configured model)
            enable_cache: Enable caching
            cache_dir: Custom cache directory
            verbose: Enable verbose output
        """
        self.console = Console()
        self.verbose = verbose
        
        # Initialize agents
        self.classifier = DocumentClassifierAgent(llm=llm)
        self.extractor = ContentExtractorAgent(llm=llm)
        self.analyzer = DocumentAnalyzer(llm=llm)
        
        # Initialize cache manager
        self.enable_cache = enable_cache
        if self.enable_cache:
            cache_dir = cache_dir or CLASSIFICATION_CONFIG["cache_dir"]
            self.cache_manager = CacheManager(cache_dir=cache_dir)
        else:
            self.cache_manager = None
    
    def process_documents(
        self,
        pdf_paths: List[str],
        output_dir: str = "outputs/intermediate"
    ) -> Dict[str, Any]:
        """
        Process a list of PDF documents through the full pipeline.
        
        Args:
            pdf_paths: List of paths to PDF files
            output_dir: Directory to save intermediate results
            
        Returns:
            Dictionary containing:
            - classifications: List of DocumentClassification
            - extractions: List of ExtractedContent
            - analysis_report: DocumentAnalysisReport
            - cache_stats: Cache statistics (if caching enabled)
        """
        
        if self.verbose:
            self.console.rule("[bold blue]📚 Document Intelligence Pipeline[/bold blue]")
            self.console.print(f"[cyan]Processing {len(pdf_paths)} documents...[/cyan]\n")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Classify documents
        classifications = self._classify_documents(pdf_paths)
        
        # Step 2: Extract content
        extractions = self._extract_content(classifications)
        
        # Step 3: Analyze document set
        analysis_report = self._analyze_documents(classifications, extractions)
        
        # Save intermediate results
        if PROCESSING_CONFIG["save_intermediate_results"]:
            self._save_intermediate_results(
                classifications,
                extractions,
                analysis_report,
                output_dir
            )
        
        # Display summary
        if self.verbose:
            self._display_pipeline_summary(
                classifications,
                extractions,
                analysis_report
            )
        
        result = {
            "classifications": classifications,
            "extractions": extractions,
            "analysis_report": analysis_report
        }
        
        if self.enable_cache and self.cache_manager:
            result["cache_stats"] = self.cache_manager.get_cache_stats()
        
        return result
    
    def _classify_documents(
        self,
        pdf_paths: List[str]
    ) -> List[DocumentClassification]:
        """Classify documents with caching."""
        
        if self.verbose:
            self.console.rule("[bold magenta]📋 Step 1: Document Classification[/bold magenta]")
        
        classifications = []
        cache_hits = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Classifying documents...",
                total=len(pdf_paths)
            )
            
            for pdf_path in pdf_paths:
                filename = os.path.basename(pdf_path)
                
                # Check cache first
                cached_classification = None
                if self.enable_cache and self.cache_manager:
                    cached_classification = self.cache_manager.get_cached_classification(pdf_path)
                
                if cached_classification:
                    classifications.append(cached_classification)
                    cache_hits += 1
                    if self.verbose:
                        self.console.print(f"   ✓ [dim]{filename}[/dim] - [green]Cached[/green] ({cached_classification.document_type})")
                else:
                    # Classify
                    classification = self.classifier.classify_document(pdf_path, filename)
                    classifications.append(classification)
                    
                    # Cache result
                    if self.enable_cache and self.cache_manager:
                        self.cache_manager.cache_classification(pdf_path, classification)
                    
                    if self.verbose:
                        self.console.print(
                            f"   ✓ {filename} - [yellow]{classification.document_type}[/yellow] "
                            f"(confidence: {classification.confidence:.2f})"
                        )
                
                progress.update(task, advance=1)
        
        if self.verbose and self.enable_cache:
            self.console.print(f"\n[dim]Cache hits: {cache_hits}/{len(pdf_paths)}[/dim]\n")
        
        return classifications
    
    def _extract_content(
        self,
        classifications: List[DocumentClassification]
    ) -> List[ExtractedContent]:
        """Extract content with caching."""
        
        if self.verbose:
            self.console.rule("[bold green]🔍 Step 2: Content Extraction[/bold green]")
        
        extractions = []
        cache_hits = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Extracting content...",
                total=len(classifications)
            )
            
            for classification in classifications:
                # Check cache first
                cached_extraction = None
                if self.enable_cache and self.cache_manager:
                    cached_extraction = self.cache_manager.get_cached_extraction(
                        classification.filepath
                    )
                
                if cached_extraction:
                    extractions.append(cached_extraction)
                    cache_hits += 1
                    if self.verbose:
                        self.console.print(
                            f"   ✓ [dim]{classification.filename}[/dim] - [green]Cached[/green]"
                        )
                else:
                    # Extract
                    extraction = self.extractor.extract_content(classification)
                    extractions.append(extraction)
                    
                    # Cache result
                    if self.enable_cache and self.cache_manager:
                        self.cache_manager.cache_extraction(
                            classification.filepath,
                            extraction
                        )
                    
                    if self.verbose:
                        self.console.print(
                            f"   ✓ {classification.filename} - "
                            f"Confidence: {extraction.extraction_confidence:.2f}"
                        )
                
                progress.update(task, advance=1)
        
        if self.verbose and self.enable_cache:
            self.console.print(f"\n[dim]Cache hits: {cache_hits}/{len(classifications)}[/dim]\n")
        
        return extractions
    
    def _analyze_documents(
        self,
        classifications: List[DocumentClassification],
        extractions: List[ExtractedContent]
    ) -> DocumentAnalysisReport:
        """Analyze document set."""
        
        if self.verbose:
            self.console.rule("[bold cyan]🔬 Step 3: Document Analysis[/bold cyan]")
        
        # Check for cached analysis
        cached_report = None
        if self.enable_cache and self.cache_manager:
            doc_set_id = self.cache_manager.generate_document_set_id(
                [c.filepath for c in classifications]
            )
            cached_report = self.cache_manager.get_cached_analysis_report(doc_set_id)
        
        if cached_report and self.verbose:
            self.console.print("[green]Using cached analysis report[/green]\n")
            return cached_report
        
        # Perform analysis
        report = self.analyzer.analyze_documents(classifications, extractions)
        
        # Cache result
        if self.enable_cache and self.cache_manager:
            doc_set_id = self.cache_manager.generate_document_set_id(
                [c.filepath for c in classifications]
            )
            self.cache_manager.cache_analysis_report(doc_set_id, report)
        
        return report
    
    def _save_intermediate_results(
        self,
        classifications: List[DocumentClassification],
        extractions: List[ExtractedContent],
        analysis_report: DocumentAnalysisReport,
        output_dir: str
    ):
        """Save intermediate results to files."""
        
        import json
        
        # Save classifications
        classifications_data = [
            {
                "filename": c.filename,
                "filepath": c.filepath,
                "document_type": c.document_type,
                "confidence": c.confidence
            }
            for c in classifications
        ]
        with open(os.path.join(output_dir, "document_classifications.json"), 'w') as f:
            json.dump(classifications_data, f, indent=2)
        
        # Save extractions
        extractions_data = [
            {
                "filename": e.filename,
                "document_type": e.document_type,
                "title": e.title,
                "summary": e.summary,
                "requirements": e.requirements,
                "features": e.features,
                "technical_details": e.technical_details,
                "extraction_confidence": e.extraction_confidence
            }
            for e in extractions
        ]
        with open(os.path.join(output_dir, "document_extractions.json"), 'w') as f:
            json.dump(extractions_data, f, indent=2)
        
        # Save analysis report (JSON and Markdown)
        self.analyzer.export_report_to_json(
            analysis_report,
            os.path.join(output_dir, "document_analysis_report.json")
        )
        self.analyzer.export_report_to_markdown(
            analysis_report,
            os.path.join(output_dir, "document_analysis_report.md")
        )
    
    def _display_pipeline_summary(
        self,
        classifications: List[DocumentClassification],
        extractions: List[ExtractedContent],
        analysis_report: DocumentAnalysisReport
    ):
        """Display summary of pipeline results."""
        
        self.console.rule("[bold blue]📊 Pipeline Summary[/bold blue]")
        
        # Classification summary
        table = Table(title="Document Classifications", show_header=True)
        table.add_column("Document", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Confidence", style="green")
        
        for classification in classifications:
            table.add_row(
                classification.filename,
                classification.document_type,
                f"{classification.confidence:.2%}"
            )
        
        self.console.print(table)
        self.console.print()
        
        # Analysis summary
        summary_panel = f"""
[bold]Coverage Score:[/bold] {analysis_report.coverage_score:.2%}
[bold]Planning Readiness:[/bold] {analysis_report.readiness_for_planning.upper()}
[bold]Confidence Score:[/bold] {analysis_report.confidence_score:.2%}

[bold]Documents Present:[/bold] {len(analysis_report.document_types_present)}
[bold]Documents Missing:[/bold] {len(analysis_report.document_types_missing)}
[bold]High Severity Conflicts:[/bold] {analysis_report.conflicts.severity_high}
[bold]Critical Questions:[/bold] {len(analysis_report.critical_questions)}
"""
        
        self.console.print(Panel(summary_panel, title="Analysis Summary", border_style="cyan"))
        self.console.print()
    
    def get_planning_context(
        self,
        pipeline_result: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive planning context from pipeline results.
        
        This context can be used by the planning agent instead of raw documents.
        
        Args:
            pipeline_result: Result from process_documents()
            
        Returns:
            Formatted string with comprehensive planning context
        """
        
        extractions: List[ExtractedContent] = pipeline_result["extractions"]
        report: DocumentAnalysisReport = pipeline_result["analysis_report"]
        
        context_parts = []
        
        # Header
        context_parts.append("# Project Planning Context")
        context_parts.append(f"\nGenerated from {len(extractions)} document(s)")
        context_parts.append(f"Coverage Score: {report.coverage_score:.2%}")
        context_parts.append(f"Planning Readiness: {report.readiness_for_planning.upper()}\n")
        
        # Document summaries
        context_parts.append("## Document Summaries\n")
        for extraction in extractions:
            context_parts.append(f"### {extraction.filename} ({extraction.document_type})\n")
            if extraction.title:
                context_parts.append(f"**Title:** {extraction.title}\n")
            if extraction.summary:
                context_parts.append(f"**Summary:** {extraction.summary}\n")
            context_parts.append("")
        
        # Requirements
        all_requirements = [req for e in extractions for req in e.requirements]
        if all_requirements:
            context_parts.append("## Requirements\n")
            for i, req in enumerate(all_requirements, 1):
                priority = req.get("priority") or "medium"
                req_type = req.get("type") or "functional"
                desc = req.get("description") or ""
                context_parts.append(f"{i}. [{priority.upper()} / {req_type}] {desc}")
            context_parts.append("")
        
        # Features
        all_features = [feat for e in extractions for feat in e.features]
        if all_features:
            context_parts.append("## Features\n")
            for i, feat in enumerate(all_features, 1):
                name = feat.get("name", "")
                desc = feat.get("description", "")
                context_parts.append(f"{i}. **{name}**: {desc}")
            context_parts.append("")
        
        # Technical Details
        context_parts.append("## Technical Context\n")
        if report.common_technologies:
            context_parts.append(f"**Technologies:** {', '.join(report.common_technologies)}")
        
        for extraction in extractions:
            if extraction.technical_details:
                td = extraction.technical_details
                if td.get("architecture"):
                    context_parts.append(f"\n**Architecture ({extraction.filename}):** {td['architecture']}")
                if td.get("technology_stack"):
                    context_parts.append(f"**Tech Stack:** {', '.join(td['technology_stack'])}")
        
        context_parts.append("")
        
        # Risks, Dependencies, Constraints
        if report.all_risks:
            context_parts.append("## Risks\n")
            for risk in report.all_risks:
                context_parts.append(f"- [{risk['source']}] {risk['risk']}")
            context_parts.append("")
        
        if report.all_dependencies:
            context_parts.append("## Dependencies\n")
            for dep in report.all_dependencies:
                context_parts.append(f"- [{dep['source']}] {dep['dependency']}")
            context_parts.append("")
        
        if report.all_constraints:
            context_parts.append("## Constraints\n")
            for con in report.all_constraints:
                context_parts.append(f"- [{con['source']}] {con['constraint']}")
            context_parts.append("")
        
        # Gaps and Missing Information
        if report.gaps.missing_document_types or report.gaps.missing_critical_info:
            context_parts.append("## Documentation Gaps\n")
            if report.gaps.missing_document_types:
                context_parts.append("**Missing Document Types:**")
                for doc_type in report.gaps.missing_document_types:
                    context_parts.append(f"- {doc_type}")
            
            if report.gaps.missing_critical_info:
                context_parts.append("\n**Missing Critical Information:**")
                for info in report.gaps.missing_critical_info:
                    context_parts.append(f"- {info}")
            
            context_parts.append("")
        
        # Critical Questions
        if report.critical_questions:
            context_parts.append("## Questions Requiring Client Clarification\n")
            for i, question in enumerate(report.critical_questions, 1):
                context_parts.append(f"{i}. {question}")
            context_parts.append("")
        
        return "\n".join(context_parts)
