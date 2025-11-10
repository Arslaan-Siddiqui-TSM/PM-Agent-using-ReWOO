"""
Feasibility Handler

Handles feasibility assessment generation using LLM.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import time

from fastapi import HTTPException

from src.core.session import Session


class FeasibilityHandler:
    """
    Handles feasibility assessment generation.
    
    Workflow:
    1. Read MD files from parsed documents
    2. Process development context (Q&A from questionnaire)
    3. Generate feasibility assessment with LLM
    4. Save reports (thinking summary + feasibility report)
    5. Return results
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize feasibility handler.
        
        Args:
            verbose: Enable verbose console output
        """
        self.verbose = verbose
    
    def generate_feasibility(
        self,
        session: Session,
        development_context: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Generate feasibility assessment using graph execution.
        
        Args:
            session: Session object
            development_context: Development process information (Q&A from questionnaire)
        
        Returns:
            Dictionary with session_id, message, file paths, execution_time
        """
        print(f"Feasibility check requested for session: {session.session_id}")
        start_time = time.time()
        
        try:
            from src.app.feasibility_agent import save_development_context_to_json
            
            # Step 1: Get MD file paths
            print("Step 1: Preparing document input for feasibility analysis")
            md_file_paths = self._get_md_file_paths(session)
            print(f"Prepared {len(md_file_paths)} MD file paths")
            
            # Step 1.5: Save development context if provided
            dev_context_json_path = None
            if development_context:
                print("Development context provided, saving to JSON")
                dev_context_json_path = save_development_context_to_json(
                    development_context=development_context,
                    session_id=session.session_id,
                    output_dir="output/intermediate"
                )
                print(f"Development context saved to JSON: {dev_context_json_path}")
            else:
                print("No development context provided.")
            
            # Step 2: Generate feasibility assessment using graph
            from src.config.feature_flags import feature_flags
            
            if feature_flags.use_hardcoded_feasibility:
                print("\n" + "="*80)
                print("HARDCODED FEASIBILITY MODE: Loading from static files")
                print("Skipping LLM calls to save costs during development/testing")
                print("="*80 + "\n")
                feasibility_result = self._load_hardcoded_feasibility()
            else:
                print("Step 2: Initializing Feasibility graph state")
                from src.states.feasibility_state import FeasibilityState
                
                feasibility_state = FeasibilityState(
                    session_id=session.session_id,
                    md_file_paths=md_file_paths,
                    development_context=development_context
                )
                
                print("Step 3: Executing Feasibility graph")
                thinking_summary, feasibility_report = self._execute_graph(feasibility_state)
                
                feasibility_result: Dict[str, str] = {
                    "thinking_summary": thinking_summary or "",
                    "feasibility_report": feasibility_report or ""
                }
            
            # Validate outputs
            self._validate_outputs(feasibility_result)
            
            # Step 4: Save both markdown files
            print("Step 4: Saving feasibility documents to files")
            thinking_path, report_path = self._save_feasibility_files(
                feasibility_result,
                session.session_id
            )
            
            # Step 5: Store in session
            print("Step 5: Storing feasibility assessment in session")
            session.feasibility_assessment = feasibility_result["feasibility_report"]
            session.feasibility_file_path = str(report_path)
            print(f"Feasibility documents stored in session")
            
            execution_time = time.time() - start_time
            print(f"Feasibility check completed in {execution_time:.2f}s")
            
            return {
                "session_id": session.session_id,
                "message": f"Feasibility assessment generated successfully. Two files created: {thinking_path.name} and {report_path.name}",
                "thinking_summary_file": str(thinking_path),
                "feasibility_report_file": str(report_path),
                "development_context_json_path": dev_context_json_path,
                "execution_time": execution_time
            }
            
        except Exception as e:
            print(f"Error during feasibility check for session {session.session_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error during feasibility check: {str(e)}"
            )
    
    def _get_md_file_paths(self, session: Session) -> list[str]:
        """
        Get list of MD file paths from the session's parsed documents directory.
        
        Used for v3 JSON conversion.
        """
        if not session.parsed_documents_dir:
            raise ValueError("No parsed documents directory found. Please ensure documents are uploaded and parsed first.")
        
        md_dir = Path(session.parsed_documents_dir)
        if not md_dir.exists():
            raise ValueError(f"MD directory not found: {md_dir}")
        
        # Find all .md files in the directory
        md_files = list(md_dir.glob("*.md"))
        
        if not md_files:
            raise ValueError(f"No MD files found in {md_dir}")
        
        print(f"Found {len(md_files)} MD files in {md_dir.name}")
        md_file_paths = [str(md_path.absolute()) for md_path in sorted(md_files)]
        
        for path in md_file_paths:
            print(f"  - {Path(path).name}")
        
        return md_file_paths
    
    def _execute_graph(self, state):
        """Execute the feasibility graph and return results."""
        from src.app.feasibility_graph import get_feasibility_graph
        
        graph = get_feasibility_graph(state)
        
        thinking_summary = None
        feasibility_report = None
        
        for s in graph.stream(state):
            node_name = next(iter(s))
            data = s[node_name]
            print(f"Completed graph node: {node_name}")
            
            thinking_summary = data.get("thinking_summary")
            feasibility_report = data.get("feasibility_report")
        
        return thinking_summary, feasibility_report
    
    def _validate_outputs(self, feasibility_result: Dict[str, str]):
        """Validate feasibility outputs are not empty."""
        def _too_short(s: str) -> bool:
            return (not s) or (len(s.strip()) < 50)
        
        if _too_short(feasibility_result.get("feasibility_report", "")) or _too_short(feasibility_result.get("thinking_summary", "")):
            print("WARNING: Feasibility outputs too short; attempting one retry generation...")
            raise HTTPException(
                status_code=502,
                detail="LLM returned insufficient content for feasibility outputs. Please try again."
            )
    
    def _load_hardcoded_feasibility(self) -> Dict[str, str]:
        """
        Load hardcoded feasibility files instead of generating with LLM.
        
        This is used for fast development/testing to avoid expensive LLM calls.
        Enable with USE_HARDCODED_FEASIBILITY=true in .env
        
        Returns:
            Dictionary with 'thinking_summary' and 'feasibility_report' keys
        """
        from src.config.feature_flags import feature_flags
        from pathlib import Path
        
        thinking_file = Path(feature_flags.hardcoded_feasibility_thinking_file)
        report_file = Path(feature_flags.hardcoded_feasibility_report_file)
        
        print(f"Loading hardcoded thinking summary from: {thinking_file}")
        if not thinking_file.exists():
            raise FileNotFoundError(
                f"Hardcoded thinking summary file not found: {thinking_file}\n"
                f"Please ensure the file exists or disable USE_HARDCODED_FEASIBILITY"
            )
        
        print(f"Loading hardcoded feasibility report from: {report_file}")
        if not report_file.exists():
            raise FileNotFoundError(
                f"Hardcoded feasibility report file not found: {report_file}\n"
                f"Please ensure the file exists or disable USE_HARDCODED_FEASIBILITY"
            )
        
        # Read files
        with open(thinking_file, 'r', encoding='utf-8') as f:
            thinking_summary = f.read()
        
        with open(report_file, 'r', encoding='utf-8') as f:
            feasibility_report = f.read()
        
        print(f"Loaded thinking summary: {len(thinking_summary)} chars")
        print(f"Loaded feasibility report: {len(feasibility_report)} chars")
        
        return {
            "thinking_summary": thinking_summary,
            "feasibility_report": feasibility_report
        }
    
    def _save_feasibility_files(
        self,
        feasibility_result: Dict[str, str],
        session_id: str
    ) -> tuple:
        """Save feasibility files to session reports folder."""
        # Use session-specific reports directory
        session_id_short = session_id[:8]
        output_dir = Path(f"output/session_{session_id_short}/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with session ID and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save thinking summary
        thinking_filename = f"thinking_summary_{session_id[:8]}_{timestamp}.md"
        thinking_path = output_dir / thinking_filename
        with open(thinking_path, "w", encoding="utf-8") as f:
            f.write(feasibility_result["thinking_summary"])
        print(f"Thinking summary saved to: {thinking_path}")
        
        # Save feasibility report
        report_filename = f"feasibility_report_{session_id[:8]}_{timestamp}.md"
        report_path = output_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(feasibility_result["feasibility_report"])
        print(f"Feasibility report saved to: {report_path}")
        
        return thinking_path, report_path

