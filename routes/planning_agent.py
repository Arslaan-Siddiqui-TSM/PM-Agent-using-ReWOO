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


class PreFeasibilityRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
    use_intelligent_processing: bool = Field(True, description="Use Document Intelligence Pipeline for processing")


class PreFeasibilityResponse(BaseModel):
    session_id: str
    questions: Dict[str, List[str]]
    message: str
    execution_time: float
    file_path: Optional[str] = Field(None, description="Path to the saved questions file")


class FeasibilityRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
    use_intelligent_processing: bool = Field(True, description="Use Document Intelligence Pipeline for processing")


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


# Endpoint 2: Generate Pre-Feasibility Questions
@router.post("/pre-feasibility-questions", response_model=PreFeasibilityResponse)
async def generate_pre_feasibility_questions_endpoint(request: PreFeasibilityRequest):
    """
    Generate strategic questions to assess project feasibility before detailed analysis.
    These questions help identify key concerns across multiple dimensions:
    - Technical Feasibility
    - Financial Viability
    - Resource Availability
    - Timeline Constraints
    - Risk Factors
    - Stakeholder Impact
    
    The generated questions will be used to guide the detailed feasibility assessment.
    """
    print(f"Pre-feasibility questions requested for session: {request.session_id}")
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
        from app.feasibility_agent import extract_text_from_pdfs, generate_pre_feasibility_questions
        
        # Step 1: Process documents
        print(f"Step 1: Processing documents (intelligent_processing={request.use_intelligent_processing})")
        
        if request.use_intelligent_processing:
            print("Using Document Intelligence Pipeline for structured processing")
            pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
            pipeline_result = pipeline.process_documents(
                session.document_paths,
                output_dir="outputs/intermediate"
            )
            
            # Store pipeline result in session for later use
            session.pipeline_result = pipeline_result
            print(f"Pipeline processed {len(pipeline_result.get('classifications', []))} documents")
            
            # Get structured context
            docs_text = pipeline.get_planning_context(pipeline_result)
            print(f"Generated structured context: {len(docs_text)} characters")
        else:
            print("Using raw text extraction")
            docs_text = extract_text_from_pdfs(session.document_paths)
            print(f"Extracted {len(docs_text)} characters from documents")
        
        # Step 2: Generate strategic questions using LLM
        print("Step 2: Generating strategic feasibility questions with LLM")
        
        max_retries = 3
        retry_delay = 5
        questions_dict = None
        
        for attempt in range(max_retries):
            try:
                questions_dict = generate_pre_feasibility_questions(docs_text)
                print("Pre-feasibility questions generated successfully")
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
                            detail=f"Google Gemini API rate limit exceeded. Please try again in a few minutes."
                        )
                else:
                    raise
        
        if questions_dict is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate pre-feasibility questions"
            )
        
        # Step 3: Save questions to file
        print("Step 3: Saving pre-feasibility questions to file")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pre_feasibility_questions_{request.session_id[:8]}_{timestamp}.md"
        file_path = output_dir / filename
        
        # Format questions as markdown
        markdown_content = "# Pre-Feasibility Assessment Questions\n\n"
        markdown_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"Session ID: {request.session_id}\n\n"
        markdown_content += "---\n\n"
        
        for category, questions in questions_dict.items():
            markdown_content += f"## {category}\n\n"
            for i, question in enumerate(questions, 1):
                markdown_content += f"{i}. {question}\n"
            markdown_content += "\n"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"Pre-feasibility questions saved to: {file_path}")
        
        # Step 4: Store in session
        print("Step 4: Storing questions in session")
        session.pre_feasibility_questions = questions_dict
        session.pre_feasibility_file_path = str(file_path)
        
        execution_time = time.time() - start_time
        print(f"Pre-feasibility questions generation completed in {execution_time:.2f}s")
        
        return PreFeasibilityResponse(
            session_id=request.session_id,
            questions=questions_dict,
            message=f"Strategic feasibility questions generated successfully and saved to {filename}",
            file_path=str(file_path),
            execution_time=execution_time
        )
        
    except Exception as e:
        print(f"Error generating pre-feasibility questions for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating pre-feasibility questions: {str(e)}"
        )


# Endpoint 3: Feasibility Check
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
        from app.feasibility_agent import extract_text_from_pdfs, generate_feasibility_questions
        
        # Step 1: Process documents with Document Intelligence Pipeline or raw extraction
        print(f"Step 1: Processing documents (intelligent_processing={request.use_intelligent_processing})")
        
        if request.use_intelligent_processing:
            print("Using Document Intelligence Pipeline for structured processing")
            # Check if we already have pipeline results
            if session.pipeline_result:
                print("Using cached Document Intelligence Pipeline results")
                pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
                docs_text = pipeline.get_planning_context(session.pipeline_result)
                print(f"Retrieved cached structured context: {len(docs_text)} characters")
            else:
                print("Running Document Intelligence Pipeline")
                pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
                pipeline_result = pipeline.process_documents(
                    session.document_paths,
                    output_dir="outputs/intermediate"
                )
                session.pipeline_result = pipeline_result
                docs_text = pipeline.get_planning_context(pipeline_result)
                print(f"Generated structured context: {len(docs_text)} characters")
        else:
            print("Using raw text extraction")
            docs_text = extract_text_from_pdfs(session.document_paths)
            print(f"Extracted {len(docs_text)} characters from {len(session.document_paths)} documents")
        
        # Step 1.5: Add pre-feasibility questions to context if available
        if session.pre_feasibility_questions:
            print("Pre-feasibility questions found in session, adding to context")
            questions_text = "\n\n## STRATEGIC FEASIBILITY QUESTIONS TO ADDRESS:\n\n"
            for category, questions in session.pre_feasibility_questions.items():
                questions_text += f"### {category}\n"
                for i, q in enumerate(questions, 1):
                    questions_text += f"{i}. {q}\n"
                questions_text += "\n"
            docs_text = docs_text + questions_text
            print("Pre-feasibility questions added to context for guided assessment")
        else:
            print("No pre-feasibility questions found. Proceeding with standard assessment.")
        
        # Step 2: Generate feasibility assessment using LLM
        print("Step 2: Generating feasibility assessment with LLM")
        
        max_retries = 3
        retry_delay = 5
        feasibility_assessment = None
        
        for attempt in range(max_retries):
            try:
                feasibility_assessment = generate_feasibility_questions(docs_text)
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
        
        if feasibility_assessment is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate feasibility assessment"
            )
        
        # Step 3: Save feasibility assessment to file
        print("Step 3: Saving feasibility assessment to file")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Create filename with session ID and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feasibility_assessment_{request.session_id[:8]}_{timestamp}.md"
        file_path = output_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(feasibility_assessment)
        
        print(f"Feasibility assessment saved to: {file_path}")
        
        # Step 4: Store feasibility assessment in session
        print("Step 4: Storing feasibility assessment in session")
        session.feasibility_assessment = feasibility_assessment
        session.feasibility_file_path = str(file_path)  # Store the file path
        print(f"Feasibility assessment stored in session with file path: {file_path}")
        
        execution_time = time.time() - start_time
        print(f"Feasibility check completed in {execution_time:.2f}s")
        
        return {
            "session_id": request.session_id,
            "message": f"Feasibility assessment generated successfully and saved to {filename}",
            "file_path": str(file_path),
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
            # Check if we already have pipeline results from feasibility check
            if session.pipeline_result:
                print("Using cached Document Intelligence Pipeline results from feasibility check")
                pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
                document_context = pipeline.get_planning_context(session.pipeline_result)
                print(f"Retrieved cached structured context: {len(document_context)} characters")
            else:
                print("Running Document Intelligence Pipeline (no cached results)")
                pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
                pipeline_result = pipeline.process_documents(
                    session.document_paths,
                    output_dir="outputs/intermediate"
                )
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

