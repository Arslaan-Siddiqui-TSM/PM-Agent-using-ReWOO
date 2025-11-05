"""
Planning Agent Routes

FastAPI endpoints for document upload, feasibility checking, and plan generation.
All business logic is delegated to handler modules for maintainability.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time

from src.core.session_storage import sessions

# Import handlers
from src.routes.upload_handler import UploadHandler
from src.routes.feasibility_handler import FeasibilityHandler
from src.routes.plan_generation_handler import PlanGenerationHandler

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class UploadResponse(BaseModel):
    session_id: str
    message: str
    uploaded_files: List[str]
    total_files: int


class GenerateEmbeddingsRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
    force_reprocess: bool = Field(False, description="Force re-parsing and re-embedding (bypass cache)")


class GenerateEmbeddingsResponse(BaseModel):
    session_id: str
    collection_name: str
    chunks_stored: int
    cache_hits: int
    cache_misses: int
    processing_time: float
    parsing_log: str


class FeasibilityRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload response")
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


# ============================================================================
# Endpoint 1: Upload Documents (Creates Session)
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    use_default_files: bool = False,
    files: Optional[List[UploadFile]] = File(None, description="PDF files to upload (max 15 files)")
):
    """
    Upload PDF documents and create a session.
    Returns a session_id to use for subsequent requests.
    
    Options:
    1. Set use_default_files=true to automatically use all PDFs from the data/files/ directory
    2. Upload your own files (if use_default_files=false)
    
    No need to manage file paths - just use the session_id!
    
    Note: Processing happens in background. Use /upload-status/{session_id} to check progress.
    """
    handler = UploadHandler(enable_rag=True, verbose=False)
    result = await handler.handle_upload(use_default_files=use_default_files, files=files)
    
    return UploadResponse(
        session_id=result["session_id"],
        message=result["message"],
        uploaded_files=result["uploaded_files"],
        total_files=result["total_files"]
    )


@router.get("/upload-status/{session_id}")
async def check_upload_status(session_id: str):
    """
    Check the processing status of uploaded documents.
    
    Returns:
        - status: pending/processing/completed/failed
        - message: Status message with details
        - parsed_documents: Number of documents parsed (if completed)
        - chunks_created: Number of vector embeddings created (if completed)
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload documents first."
        )
    
    response = {
        "session_id": session_id,
        "status": session.processing_status,
        "message": session.status_message,
        "created_at": session.created_at.isoformat(),
    }
    
    # Add detailed info if processing is completed
    if session.processing_status == "completed" and session.parsed_documents:
        response["parsed_documents"] = len(session.parsed_documents)
        if session.embedding_cache_stats:
            response["chunks_created"] = session.embedding_cache_stats.get("session_cache_misses", 0)
            response["cache_hits"] = session.embedding_cache_stats.get("session_cache_hits", 0)
        if session.qdrant_collection_name:
            response["qdrant_collection"] = session.qdrant_collection_name
    
    # Add error details if processing failed
    if session.processing_status == "failed" and session.processing_error:
        response["error"] = session.processing_error
    
    return response


# ============================================================================
# Endpoint 2: Generate Embeddings (Manual RAG Processing)
# ============================================================================

@router.post("/generate-embeddings", response_model=GenerateEmbeddingsResponse)
async def generate_embeddings(request: GenerateEmbeddingsRequest):
    """
    Manually trigger or force re-generate embeddings for a session's documents.
    Useful for:
    - Re-processing documents with updated settings
    - Force bypassing cache
    - Regenerating embeddings after errors
    
    The upload endpoint already processes embeddings automatically,
    so this is only needed for special cases.
    """
    print(f"Generate embeddings requested for session: {request.session_id}")
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
    
    if not session.document_paths:
        raise HTTPException(
            status_code=400,
            detail="No documents found in session. Please upload documents first."
        )
    
    try:
        print(f"Processing {len(session.document_paths)} documents with force_reprocess={request.force_reprocess}")
        
        # STEP 1: Parse PDFs → MD files
        from src.core.docling_parser import DoclingParser
        parser = DoclingParser(
            session_id=request.session_id,
            output_dir="output",
            ocr_enabled=True,  # OCR for scanned documents
            table_mode="fast",  # Fast mode: 20-30s per PDF
            enable_cache=True
        )
        parsing_result = parser.parse_pdfs(
            pdf_paths=session.document_paths,
            force_reparse=request.force_reprocess
        )
        
        # STEP 2: Embed MD files → Qdrant
        from src.core.embedding_handler import EmbeddingHandler
        from src.config.feature_flags import feature_flags
        
        embedding_handler = EmbeddingHandler(
            session_id=request.session_id,
            qdrant_url=feature_flags.qdrant_url,
            embedding_model=(
                feature_flags.gemini_embedding_model 
                if feature_flags.embedding_provider == "gemini" 
                else feature_flags.embedding_model
            ),
            embedding_provider=feature_flags.embedding_provider,
            chunk_size=feature_flags.max_chunk_size,
            chunk_overlap=feature_flags.chunk_overlap,
            verbose=True
        )
        embedding_result = embedding_handler.embed_documents(
            parsed_documents=parsing_result["parsed_documents"],
            cached_documents_info=[]  # Not needed with new simple parser
        )
        
        # Update session
        session.parsed_documents = parsing_result["parsed_documents"]
        session.qdrant_manager = embedding_result["qdrant_manager"]
        session.qdrant_collection_name = embedding_result["qdrant_collection_name"]
        session.embedding_cache_stats = embedding_result["cache_stats"]
        session.parsing_log_path = parsing_result["parsing_log_path"]
        
        execution_time = time.time() - start_time
        
        print(f"Embedding generation complete in {execution_time:.2f}s")
        print(f"  - Collection: {embedding_result['qdrant_collection_name']}")
        print(f"  - Chunks: {embedding_result['chunks_added']}")
        print(f"  - Cache hits: {embedding_result['cache_stats'].get('session_cache_hits', 0)}")
        
        return GenerateEmbeddingsResponse(
            session_id=request.session_id,
            collection_name=embedding_result["qdrant_collection_name"],
            chunks_stored=embedding_result["chunks_added"],
            cache_hits=embedding_result["cache_stats"].get("session_cache_hits", 0),
            cache_misses=embedding_result["cache_stats"].get("session_cache_misses", 0),
            processing_time=execution_time,
            parsing_log=parsing_result["parsing_log_path"]
        )
    except Exception as e:
        print(f"Error during embedding generation for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during embedding generation: {str(e)}"
        )


# ============================================================================
# Endpoint 3: Feasibility Check
# ============================================================================

@router.post("/feasibility")
async def check_feasibility(request: FeasibilityRequest):
    """
    Generate feasibility assessment using LLM based on uploaded documents.
    Just provide the session_id from upload - no file paths needed!
    Returns the feasibility assessment in markdown format.
    
    IMPORTANT: This endpoint requires that document processing (parsing, JSON conversion, 
    and embedding) is fully complete before feasibility generation can proceed.
    """
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
    
    # CRITICAL: Validate that all processing is complete before feasibility generation
    if session.processing_status != "completed":
        print(f"Processing not complete for session {request.session_id}: status={session.processing_status}")
        
        if session.processing_status == "processing":
            raise HTTPException(
                status_code=425,  # Too Early
                detail=(
                    "Document processing is still in progress. "
                    "Please wait for parsing, JSON conversion, and embedding to complete. "
                    "Use /upload-status/{session_id} to check progress."
                )
            )
        elif session.processing_status == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {session.processing_error or 'Unknown error'}"
            )
        else:  # pending or other status
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Document processing has not started or is in invalid state: {session.processing_status}. "
                    "Please upload documents first."
                )
            )
    
    # Validate required session data is present
    if not session.parsed_documents or not session.qdrant_manager:
        print(f"Session {request.session_id} marked complete but missing required data")
        raise HTTPException(
            status_code=500,
            detail="Session processing incomplete: missing parsed documents or embeddings. Please re-upload documents."
        )
    
    print(f"✅ All processing complete for session {request.session_id}, proceeding with feasibility generation")
    
    # Delegate to handler
    handler = FeasibilityHandler(verbose=False)
    result = handler.generate_feasibility(
        session=session,
        development_context=request.development_context
    )
    
    return result


# ============================================================================
# Endpoint 4: Generate Full Plan
# ============================================================================

@router.post("/generate-plan", response_model=GeneratePlanResponse)
async def generate_plan(request: GeneratePlanRequest):
    """
    Generate a complete project plan based on the uploaded documents.
    Just provide the session_id - the system remembers your documents!
    
    IMPORTANT: This endpoint requires that document processing (parsing, JSON conversion, 
    and embedding) is fully complete before plan generation can proceed.
    """
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
    
    # CRITICAL: Validate that all processing is complete before plan generation
    if session.processing_status != "completed":
        print(f"Processing not complete for session {request.session_id}: status={session.processing_status}")
        
        if session.processing_status == "processing":
            raise HTTPException(
                status_code=425,  # Too Early
                detail=(
                    "Document processing is still in progress. "
                    "Please wait for parsing, JSON conversion, and embedding to complete. "
                    "Use /upload-status/{session_id} to check progress."
                )
            )
        elif session.processing_status == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {session.processing_error or 'Unknown error'}"
            )
        else:  # pending or other status
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Document processing has not started or is in invalid state: {session.processing_status}. "
                    "Please upload documents first."
                )
            )
    
    # Validate required session data is present
    if not session.parsed_documents or not session.qdrant_manager:
        print(f"Session {request.session_id} marked complete but missing required data")
        raise HTTPException(
            status_code=500,
            detail="Session processing incomplete: missing parsed documents or embeddings. Please re-upload documents."
        )
    
    print(f"✅ All processing complete for session {request.session_id}, proceeding with plan generation")
    
    # Delegate to handler
    handler = PlanGenerationHandler(verbose=False)
    result = handler.generate_plan(
        session=session,
        max_iterations=request.max_iterations,
        use_intelligent_processing=request.use_intelligent_processing
    )
    
    return GeneratePlanResponse(
        session_id=result["session_id"],
        plan=result["plan"],
        evidence=result["evidence"],
        result=result["result"],
        file_path=result["file_path"],
        steps=result["steps"],
        execution_time=result["execution_time"],
        iterations_completed=result["iterations_completed"],
        status=result["status"]
    )
