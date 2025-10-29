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
from states.rewoo_state import ReWOO
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


class GeneratePlanRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
    use_intelligent_processing: bool = Field(True, description="Use Document Intelligence Pipeline for processing")


class GeneratePlanResponse(BaseModel):
    session_id: str
    plan: Dict[str, Any]
    evidence: Dict[str, Any]
    result: str
    steps: List[str]
    execution_time: float


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
        from app.feasibility_agent import extract_text_from_pdfs, generate_feasibility_questions
        
        # Step 1: Process documents with Document Intelligence Pipeline or raw extraction
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
            
            # Get structured planning context from pipeline
            docs_text = pipeline.get_planning_context(pipeline_result)
            print(f"Generated structured context: {len(docs_text)} characters")
        else:
            print("Using raw text extraction")
            docs_text = extract_text_from_pdfs(session.document_paths)
            print(f"Extracted {len(docs_text)} characters from {len(session.document_paths)} documents")
        
        # Step 2: Generate feasibility assessment using LLM
        print("Step 2: Generating feasibility assessment with LLM")
        feasibility_assessment = generate_feasibility_questions(docs_text)
        print("Feasibility assessment generated")
        
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
        
        # Step 3: Initialize ReWOO state
        print("Step 3: Initializing ReWOO state")
        rewoo_state = ReWOO(
            document_context=document_context,
            plan_string=None,
            result=None,
            feasibility_file_path=session.feasibility_file_path  # Pass the file path to state
        )
        
        # Step 4: Execute the ReWOO graph
        print("Step 4: Executing ReWOO graph")
        graph = get_graph(rewoo_state)
        final_state = graph.invoke(rewoo_state)
        print("ReWOO graph execution completed")
        
        execution_time = time.time() - start_time
        print(f"Plan generation completed in {execution_time:.2f}s")
        
        # Extract information from final state (graph returns a dict)
        steps = []
        if final_state.get('steps'):
            steps = [f"{step[0]} - {step[1]} = {step[2]}[{step[3]}]" for step in final_state.get('steps', [])]
        
        plan_dict = {
            "plan_string": final_state.get('plan_string', ""),
            "steps": steps
        }
        
        evidence_dict = final_state.get('results', {})
        
        result_str = final_state.get('result', "No result generated")
        
        return GeneratePlanResponse(
            session_id=request.session_id,
            plan=plan_dict,
            evidence=evidence_dict,
            result=result_str,
            steps=steps,
            execution_time=execution_time
        )
        
    except Exception as e:
        print(f"Error during plan generation for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during plan generation: {str(e)}"
        )

