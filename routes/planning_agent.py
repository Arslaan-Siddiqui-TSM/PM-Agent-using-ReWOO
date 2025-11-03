from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from pathlib import Path
import shutil
import uuid
from datetime import datetime

from core.session import Session
from core.session_storage import sessions
from utils.constants import UPLOAD_DIR

# Import your existing components
from app.graph import get_graph
from states.reflection_state import ReflectionState
from core.document_intelligence_pipeline import DocumentIntelligencePipeline

router = APIRouter()


# Request/Response Models
class UploadResponse(BaseModel):
    session_id: str
    message: str
    uploaded_files: List[str]
    total_files: int


class FeasibilityRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
    use_intelligent_processing: bool = Field(True, description="Use Document Intelligence Pipeline for processing")
    development_context: Optional[Dict[str, str]] = Field(None, description="Development process information from user (methodology, team size, timeline, etc.)")


class GeneratePlanRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
    use_intelligent_processing: bool = Field(True, description="Use Document Intelligence Pipeline for processing")
    max_iterations: int = Field(5, description="Maximum number of reflection iterations (default: 5)", ge=1, le=10)


class GeneratePlanResponse(BaseModel):
    session_id: str
    plan: Dict[str, Any]
    evidence: Dict[str, Any]
    result: str
    file_path: Optional[str] = Field(None, description="Path to the saved final project plan markdown file")
    steps: List[str]
    execution_time: float
    iterations_completed: int = Field(description="Number of reflection iterations completed")
    status: str = Field(description="Status of plan generation (completed/partial)")


# Endpoint 1: Upload Documents (Creates Session)
@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    use_default_files: bool = False,
    files: Optional[List[UploadFile]] = File(None, description="PDF files to upload (max 15 files)")
):
    """
    Upload PDF documents and create a session.
    Returns a session_id to use for subsequent requests.
    
    Options:
    1. Set use_default_files=true to automatically use all PDFs from the files/ directory
    2. Upload your own files (if use_default_files=false)
    
    No need to manage file paths - just use the session_id!
    """
    # Create new session
    session_id = str(uuid.uuid4())
    print(f"Created new session: {session_id}")
    session = Session(session_id)
    
    uploaded_files = []
    
    try:
        # Option 1: Use default files from files/ directory
        if use_default_files:
            print(f"Using default files from files/ directory for session {session_id}")
            import glob
            files_dir = Path("files")
            default_pdf_files = list(files_dir.glob("*.pdf"))
            
            if not default_pdf_files:
                raise HTTPException(
                    status_code=404,
                    detail="No default PDF files found in files/ directory"
                )
            
            if len(default_pdf_files) > 15:
                raise HTTPException(
                    status_code=400,
                    detail=f"Too many default files ({len(default_pdf_files)}). Maximum 15 files allowed."
                )
            
            print(f"Found {len(default_pdf_files)} default PDF files")
            for pdf_path in default_pdf_files:
                # Use the files directly without copying
                session.document_paths.append(str(pdf_path.absolute()))
                uploaded_files.append(pdf_path.name)
                print(f"Added default file: {pdf_path.name}")
        
        # Option 2: Upload custom files
        else:
            if not files or len(files) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No files provided. Either upload files or set use_default_files=true"
                )
            
            print(f"Upload endpoint called with {len(files)} files")
            
            if len(files) > 15:
                raise HTTPException(
                    status_code=400,
                    detail="Maximum 15 files allowed per upload"
                )
            
            print(f"Starting file upload for session {session_id}")
            for file in files:
                print(f"Processing file: {file.filename}")
                
                # Validate file type
                if not file.filename or not file.filename.lower().endswith('.pdf'):
                    print(f"Invalid file type rejected: {file.filename}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Only PDF files are allowed. Invalid file: {file.filename}"
                    )
                
                # Generate unique filename
                file_id = str(uuid.uuid4())[:8]
                safe_filename = f"{session_id}_{file_id}_{file.filename}"
                file_path = UPLOAD_DIR / safe_filename
                print(f"Saving file to: {file_path}")
                
                # Save file
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Store path in session
                session.document_paths.append(str(file_path))
                uploaded_files.append(file.filename)
                print(f"Successfully uploaded: {file.filename}")
        
        # Store session
        sessions[session_id] = session
        print(f"Session {session_id} stored with {len(uploaded_files)} files")
        
        message = (
            f"Using {len(uploaded_files)} default files from files/ directory. "
            "Use this session_id for feasibility check and plan generation."
            if use_default_files
            else "Files uploaded successfully. Use this session_id for feasibility check and plan generation."
        )
        
        return UploadResponse(
            session_id=session_id,
            message=message,
            uploaded_files=uploaded_files,
            total_files=len(uploaded_files)
        )
        
    except HTTPException:
        print(f"HTTPException during upload for session {session_id}")
        # Clean up any uploaded files if there's an error
        for doc_path in session.document_paths:
            file_path = Path(doc_path)
            if file_path.exists():
                file_path.unlink()
        raise
        
    except Exception as e:
        print(f"Error during file upload for session {session_id}: {str(e)}")
        # Clean up any uploaded files if there's an error
        for doc_path in session.document_paths:
            file_path = Path(doc_path)
            if file_path.exists():
                file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Error during file upload: {str(e)}"
        )


# Endpoint 2: Feasibility Check
@router.post("/feasibility")
async def check_feasibility(request: FeasibilityRequest):
    """
    Generate feasibility assessment using LLM based on uploaded documents.
    Just provide the session_id from upload - no file paths needed!
    Returns the feasibility assessment in markdown format.
    """
    print(f"Feasibility check requested for session: {request.session_id}")
    start_time = time.time()
    
    # Get session
    session = sessions.get(request.session_id)
    if not session:
        print(f"Session not found: {request.session_id}")
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload documents first."
        )
    
    if session.is_expired():
        print(f"Session expired: {request.session_id}")
        raise HTTPException(
            status_code=410,
            detail="Session expired. Please upload documents again."
        )
    
    try:
        # Import the feasibility functions
        from app.feasibility_agent import extract_text_from_pdfs, generate_feasibility_questions, save_development_context_to_json
        
        # Step 1: Process documents with Document Intelligence Pipeline or raw extraction
        print(f"Step 1: Processing documents (intelligent_processing={request.use_intelligent_processing})")
        
        if request.use_intelligent_processing:
            print("Using Document Intelligence Pipeline for structured processing")
            print(f"DOCUMENT PATHS: {session.document_paths}, SESSION PIPELINE RESULT: {session.pipeline_result}")
            
            # Initialize pipeline once
            pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
            
            # Check if we already have pipeline results
            if session.pipeline_result:
                print("Using cached Document Intelligence Pipeline results")
                print(f"DEBUG: Pipeline result keys: {session.pipeline_result.keys()}")
                print(f"DEBUG: Number of extractions: {len(session.pipeline_result.get('extractions', []))}")
                print(f"DEBUG: Number of classifications: {len(session.pipeline_result.get('classifications', []))}")
                
                docs_text = pipeline.get_planning_context(session.pipeline_result)
                print(f"Retrieved cached structured context: {len(docs_text)} characters")
            else:
                print("Running Document Intelligence Pipeline")
                print(f"DEBUG: Processing {len(session.document_paths)} documents:")
                for i, path in enumerate(session.document_paths, 1):
                    print(f"  {i}. {Path(path).name}")
                
                pipeline_result = pipeline.process_documents(
                    session.document_paths,
                    output_dir="outputs/intermediate"
                )
                
                print(f"DEBUG: Pipeline completed successfully")
                print(f"DEBUG: Pipeline result keys: {pipeline_result.keys()}")
                print(f"DEBUG: Number of extractions: {len(pipeline_result.get('extractions', []))}")
                print(f"DEBUG: Number of classifications: {len(pipeline_result.get('classifications', []))}")
                
                session.pipeline_result = pipeline_result
                docs_text = pipeline.get_planning_context(pipeline_result)
                print(f"Generated structured context: {len(docs_text)} characters")
        else:
            print("Using raw text extraction")
            docs_text = extract_text_from_pdfs(session.document_paths)
            print(f"Extracted {len(docs_text)} characters from {len(session.document_paths)} documents")
        
        # Step 1.5: Add development process information if provided
        if request.development_context:
            print("Development context provided, integrating into assessment")
            print(f"DEBUG: Development context fields provided: {list(request.development_context.keys())}")
            
            # Step 1.5a: Save development context to JSON file
            print("Step 1.5a: Saving development context to JSON file")
            dev_context_json_path = save_development_context_to_json(
                development_context=request.development_context,
                session_id=request.session_id,
                output_dir="outputs/intermediate"
            )
            print(f"Development context saved to JSON: {dev_context_json_path}")
            
            dev_context_text = "\n\n## DEVELOPMENT PROCESS INFORMATION:\n\n"
            dev_context_text += "The following information about the software development process has been provided:\n\n"
            
            context_labels = {
                "methodology": "Development Methodology",
                "teamSize": "Team Size",
                "timeline": "Project Timeline",
                "budget": "Budget Constraints",
                "techStack": "Technology Stack",
                "constraints": "Key Constraints or Risks"
            }
            
            for key, value in request.development_context.items():
                if value and value.strip():
                    label = context_labels.get(key, key.replace("_", " ").title())
                    dev_context_text += f"**{label}:** {value}\n\n"
                    print(f"DEBUG:   - {label}: {value[:100]}{'...' if len(value) > 100 else ''}")
            
            docs_text = docs_text + dev_context_text
            print(f"Development context added to assessment: {len(dev_context_text)} characters")
            
            # Store development context in session for later use
            session.development_context = request.development_context
            session.development_context_json_path = dev_context_json_path
        else:
            print("No development context provided. Proceeding without development process information.")
        
        # Step 2: Generate feasibility assessment using LLM
        print("Step 2: Generating feasibility assessment with LLM (including development context if provided)")
        
        # DEBUG: Show what context is being sent to the LLM
        print("\n" + "="*80)
        print("DEBUG: CONTEXT BEING SENT TO LLM FOR FEASIBILITY ASSESSMENT")
        print("="*80)
        print(f"Total document context length: {len(docs_text)} characters")
        print(f"Development context provided: {request.development_context is not None}")
        if request.development_context:
            print(f"Development context keys: {list(request.development_context.keys())}")
        print("="*80 + "\n")
        
        max_retries = 3
        retry_delay = 5
        feasibility_assessment = None
        
        for attempt in range(max_retries):
            try:
                # Pass development_context and session_id to the function
                # Returns dict with 'thinking_summary' and 'feasibility_report' keys
                feasibility_result = generate_feasibility_questions(
                    document_text=docs_text,
                    development_context=request.development_context,
                    session_id=request.session_id
                )
                print("Feasibility assessment generated")
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        print(f"Max retries reached. Rate limit still active.")
                        raise HTTPException(
                            status_code=429,
                            detail=f"Google Gemini API rate limit exceeded during feasibility check. Please try again in a few minutes."
                        )
                else:
                    # Not a rate limit error, re-raise immediately
                    raise
        
        if feasibility_result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate feasibility assessment"
            )

        # Guard: if outputs are empty or too short, try one more regeneration and then bail with error
        def _too_short(s: str) -> bool:
            return (not s) or (len(s.strip()) < 50)

        if _too_short(feasibility_result.get("feasibility_report", "")) or _too_short(feasibility_result.get("thinking_summary", "")):
            print("WARNING: Feasibility outputs too short; attempting one retry generation...")
            try:
                feasibility_result_retry = generate_feasibility_questions(
                    document_text=docs_text,
                    development_context=request.development_context,
                    session_id=request.session_id
                )
                if feasibility_result_retry and not (_too_short(feasibility_result_retry.get("feasibility_report", "")) or _too_short(feasibility_result_retry.get("thinking_summary", ""))):
                    feasibility_result = feasibility_result_retry
                    print("Retry succeeded with non-empty outputs")
                else:
                    print("Retry still produced empty/insufficient content; aborting without writing files")
                    raise HTTPException(
                        status_code=502,
                        detail="LLM returned insufficient content for feasibility outputs. Please try again."
                    )
            except HTTPException:
                raise
            except Exception as e:
                print(f"Retry generation failed: {e}")
                raise HTTPException(
                    status_code=502,
                    detail="LLM invocation failed to produce usable content."
                )
        
        # Step 3: Save both markdown files
        print("Step 3: Saving feasibility documents to files")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Create filename with session ID and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save thinking summary
        thinking_filename = f"thinking_summary_{request.session_id[:8]}_{timestamp}.md"
        thinking_path = output_dir / thinking_filename
        with open(thinking_path, "w", encoding="utf-8") as f:
            f.write(feasibility_result["thinking_summary"])
        print(f"Thinking summary saved to: {thinking_path}")
        
        # Save feasibility report
        report_filename = f"feasibility_report_{request.session_id[:8]}_{timestamp}.md"
        report_path = output_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(feasibility_result["feasibility_report"])
        print(f"Feasibility report saved to: {report_path}")
        
        # Step 4: Store in session (store the main report)
        print("Step 4: Storing feasibility assessment in session")
        session.feasibility_assessment = feasibility_result["feasibility_report"]
        session.feasibility_file_path = str(report_path)
        session.thinking_summary = feasibility_result["thinking_summary"]
        session.thinking_summary_file_path = str(thinking_path)
        print(f"Feasibility documents stored in session")
        
        execution_time = time.time() - start_time
        print(f"Feasibility check completed in {execution_time:.2f}s")
        
        return {
            "session_id": request.session_id,
            "message": f"Feasibility assessment generated successfully. Two files created: {thinking_filename} and {report_filename}",
            "thinking_summary_file": str(thinking_path),
            "feasibility_report_file": str(report_path),
            "development_context_json_path": getattr(session, 'development_context_json_path', None),
            "execution_time": execution_time
        }
        
    except Exception as e:
        print(f"Error during feasibility check for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during feasibility check: {str(e)}"
        )


# Endpoint 3: Generate Full Plan
@router.post("/generate-plan", response_model=GeneratePlanResponse)
async def generate_plan(request: GeneratePlanRequest):
    """
    Generate a complete project plan based on the uploaded documents.
    Just provide the session_id - the system remembers your documents!
    """
    print(f"Plan generation requested for session: {request.session_id}")
    start_time = time.time()
    
    # Get session
    session = sessions.get(request.session_id)
    if not session:
        print(f"Session not found: {request.session_id}")
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload documents first."
        )
    
    if session.is_expired():
        print(f"Session expired: {request.session_id}")
        raise HTTPException(
            status_code=410,
            detail="Session expired. Please upload documents again."
        )
    
    try:
        # Import necessary functions
        from app.feasibility_agent import extract_text_from_pdfs
        
        # Step 1: Extract or retrieve document context
        print(f"Step 1: Processing document context (intelligent_processing={request.use_intelligent_processing})")
        
        if request.use_intelligent_processing:
            # Initialize pipeline once
            pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
            
            # Check if we already have pipeline results from feasibility check
            if session.pipeline_result:
                print("Using cached Document Intelligence Pipeline results from feasibility check")
                print(f"DEBUG: Pipeline result keys: {session.pipeline_result.keys()}")
                print(f"DEBUG: Number of extractions: {len(session.pipeline_result.get('extractions', []))}")
                print(f"DEBUG: Number of classifications: {len(session.pipeline_result.get('classifications', []))}")
                
                document_context = pipeline.get_planning_context(session.pipeline_result)
                print(f"Retrieved cached structured context: {len(document_context)} characters")
            else:
                print("Running Document Intelligence Pipeline (no cached results)")
                print(f"DEBUG: Processing {len(session.document_paths)} documents:")
                for i, path in enumerate(session.document_paths, 1):
                    print(f"  {i}. {Path(path).name}")
                
                pipeline_result = pipeline.process_documents(
                    session.document_paths,
                    output_dir="outputs/intermediate"
                )
                
                print(f"DEBUG: Pipeline completed successfully")
                print(f"DEBUG: Pipeline result keys: {pipeline_result.keys()}")
                print(f"DEBUG: Number of extractions: {len(pipeline_result.get('extractions', []))}")
                print(f"DEBUG: Number of classifications: {len(pipeline_result.get('classifications', []))}")
                
                session.pipeline_result = pipeline_result
                document_context = pipeline.get_planning_context(pipeline_result)
                print(f"Generated structured context: {len(document_context)} characters")
        else:
            print("Using raw text extraction")
            document_context = extract_text_from_pdfs(session.document_paths)
            print(f"Extracted raw context: {len(document_context)} characters")
        
        # Step 2: Combine document context with feasibility assessment
        print("Step 2: Combining document context with feasibility assessment")
        
        if session.feasibility_assessment:
            print("Feasibility assessment found in session, appending to context")
            document_context = f"""{document_context}

---

## FEASIBILITY ASSESSMENT

{session.feasibility_assessment}
"""
            print(f"Combined context length: {len(document_context)} chars")
        else:
            print("WARNING: No feasibility assessment found in session. Proceeding with document context only.")
            print("Consider running /feasibility endpoint first for better results.")
        
        # Step 3: Initialize Reflection state
        print(f"Step 3: Initializing Reflection state with max_iterations={request.max_iterations}")
        
        # DEBUG: Show what context is being sent to the LLM for plan generation
        print("\n" + "="*80)
        print("DEBUG: CONTEXT BEING SENT TO LLM FOR PROJECT PLAN GENERATION")
        print("="*80)
        print(f"Total document context length: {len(document_context)} characters")
        print(f"Has feasibility assessment: {session.feasibility_assessment is not None}")
        print(f"Feasibility file path: {session.feasibility_file_path}")
        print(f"\nDocument context structure:")
        # Show section headers to understand structure
        lines = document_context.split('\n')
        section_headers = [line for line in lines if line.startswith('#')]
        print(f"Found {len(section_headers)} section headers:")
        for header in section_headers[:20]:  # Show first 20 headers
            print(f"  {header}")
        if len(section_headers) > 20:
            print(f"  ... and {len(section_headers) - 20} more sections")
        
        print(f"\nContext preview (first 3000 chars):\n{document_context[:3000]}")
        print("..." if len(document_context) > 3000 else "")
        print(f"\nContext preview (last 1500 chars):\n...{document_context[-1500:]}")
        print("="*80 + "\n")
        
        reflection_state = ReflectionState(
            task="Synthesize all provided project documents and feasibility notes into an executive-grade implementation plan.",
            document_context=document_context,
            feasibility_file_path=session.feasibility_file_path,
            max_iterations=request.max_iterations,
        )
        
        # Step 4: Execute the Reflection graph with streaming
        print("Step 4: Executing Reflection graph with streaming")
        graph = get_graph(reflection_state)
        
        final_plan_text = None
        iterations_count = 0
        node_count = 0
        
        try:
            for s in graph.stream(reflection_state):
                node_name = next(iter(s))
                data = s[node_name]
                node_count += 1
                print(f"Completed node {node_count}: {node_name}")
                
                # Capture the final plan when the revise node sets it
                if node_name == "revise":
                    final_plan_text = data.get("final_plan")
                    iterations = data.get("iterations", [])
                    iterations_count = len(iterations)
                    if final_plan_text:
                        print(f"Final plan captured from revise node after {iterations_count} iterations")
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Resource exhausted" in error_msg:
                print(f"Rate limit error during graph execution: {error_msg}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Google Gemini API rate limit exceeded. Please try again in a few minutes."
                )
            else:
                print(f"Error during graph execution: {error_msg}")
                raise
        
        if not final_plan_text:
            print("ERROR: No final plan was captured during execution")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate final plan. Please check that max_iterations allows enough cycles."
            )
        
        execution_time = time.time() - start_time
        print(f"Plan generation completed in {execution_time:.2f}s with {iterations_count} iterations")
        
        result_str = final_plan_text
        
        # Legacy response format for API compatibility
        plan_dict = {
            "plan_string": f"Reflection-based plan generated in {iterations_count} iterations.",
            "steps": []
        }
        
        evidence_dict = {"iterations": iterations_count}

        # Persist the final result to a markdown file
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_filename = f"project_plan_{request.session_id[:8]}_{ts}.md"
        plan_filepath = output_dir / plan_filename
        try:
            with plan_filepath.open("w", encoding="utf-8") as f:
                f.write(str(result_str).strip())
            print(f"Final project plan saved to: {plan_filepath}")
        except Exception as e:
            print(f"WARNING: Failed to write project plan file: {e}")
            plan_filepath = None

        return GeneratePlanResponse(
            session_id=request.session_id,
            plan=plan_dict,
            evidence=evidence_dict,
            result=result_str,
            file_path=str(plan_filepath) if plan_filepath else None,
            steps=[],
            execution_time=execution_time,
            iterations_completed=iterations_count,
            status="completed"
        )
        
    except Exception as e:
        print(f"Error during plan generation for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during plan generation: {str(e)}"
        )

